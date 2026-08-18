# Authorization boundary delle Student API federate

## Stato

Implementato da #706. La verifica integrata sulla root/installazione unica resta dipendente da #705.

## Modello

Le Student API federate separano autenticazione, scope e accesso ai dati:

1. il bearer TUI verificato produce esclusivamente il `user_id` auth interno;
2. `read_student_binding_snapshot(user_id)` legge atomicamente account, binding, membership, classi e alias;
3. `resolve_student_identity` verifica account studente attivo, binding univoco e classi/membership coerenti;
4. ogni assignment viene riletto dallo storage server in modalità strict;
5. `resolve_assignment_target` collega assignment, classe e target al `subject_id` dello snapshot;
6. il servizio applicativo riceve una copia del record e del target già autorizzati e non riesegue selezioni tramite ID client.

`StudentRequestAuthorization` è immutabile e locale a una sola richiesta. Ogni richiesta, incluso un retry con lo stesso bearer, legge un nuovo snapshot: revoca membership, classe inattiva, account disabilitato, pending o cambio ruolo hanno quindi effetto dalla richiesta successiva. `authority_revision` viene ricalcolata dai resolver #702; mismatch e storage incoerente falliscono chiusi.

Il `student_id` restituito per compatibilità TUI è un alias legacy esplicito e univoco, quando disponibile, oppure un'etichetta opaca derivata dal `subject_id`. È solo metadata operativo/presentazionale: non rientra mai in una decisione di autorizzazione. Email, dominio, username, path, repository, `student_id`, `class_id` e `subject_id` della request non determinano lo scope.

## Matrice route

| Route | Operazione | Input client ammesso | Requisito di autorizzazione | Dati usati dal servizio |
|---|---|---|---|---|
| `GET /api/student-lab/me` | read identità | nessuno | bearer valido; account student attivo; binding univoco attivo; almeno una membership student verso classe attiva | alias pubblico derivato dallo snapshot |
| `GET /api/student-lab/assignments` | read collezione | `now` solo nel contesto locale già consentito | stesso scope; lettura strict di tutti i record; filtro per classe e target risolto | sole coppie assignment/target autorizzate |
| `GET /api/student-lab/help-history` | read target | `assignment_id` come selettore | record riletto server-side; ID esatto; `resolve_assignment_target` positivo | record e target autorizzati; log server keyed dal `subject_id` |
| `POST /api/student-lab/help` | write target | `assignment_id`, tipo, prompt, request id | come help-history; gli eventuali ID identitari aggiuntivi sono ignorati | record e target già autorizzati; chiave lock/log server-side |
| `POST /api/student-lab/final-attempt` | write target | `assignment_id`, `attempt_id` | come help-history | record e target già autorizzati; tentativo operativo selezionato nella consegna |

Non sono state trovate altre route Student Lab federate: `REMOTE_STUDENT_API_ROUTES` è la allowlist canonica e contiene esattamente le cinque righe sopra. Le API dashboard/docente e i consumer CLI locali non federati restano su boundary separati.

## Failure model

- Cross-class e target altrui non vengono inclusi nelle collezioni e sono negati sulle route target-specifiche.
- Binding mancante/duplicato, alias ambiguo, membership assente, classe inattiva, account/ruolo non validi e revision mismatch producono `403` sanitizzato.
- Lettura snapshot o assignment indisponibile/corrotta produce failure sanitizzato (`503` dove classificabile come infrastruttura).
- Le risposte di errore non contengono ID, path o dati persistiti.
- I log federati contengono soltanto route allowlisted e reason code bounded; non contengono bearer, user/subject/student/assignment ID o dettagli storage/provider.
- Il fallback HMAC locale conserva la compatibilità storica ma non è attivabile quando il runtime federato è presente e non acquisisce lo scope federato.

## Implementazione

- Boundary/policy: `scripts/student_api_authorization.py`.
- HTTP enforcement: `scripts/course_board_server.py`.
- Consumer di record/target già autorizzati: `scripts/student_lab_service.py`.
- Lettura assignment strict: `JsonAssignmentRecordStorage.list_assignments_strict` e `read_assignment_strict` in `scripts/assignment_records.py`.
- Binding canonico riusato: [`adr-authoritative-student-identity-binding.md`](adr-authoritative-student-identity-binding.md).

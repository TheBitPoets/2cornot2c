# Mapping team GitHub e onboarding classi

## Scopo

`thebitlab_github_team_mapping.py` traduce snapshot completi della directory GitHub in mapping verso classi interne. Il provider non assegna direttamente ruoli o ID TheBitLab: organization e team restano riferimenti esterni numerici e rinominabili.

Questo incremento usa una porta e un fake. Il futuro adapter GitHub App dovrà produrre lo stesso snapshot senza esporre installation token al dominio.

## Mapping amministrativo

Solo un account persistito, attivo e con ruolo `admin` può creare, rinominare o eliminare un mapping. La transazione SQLite ricontrolla:

- revisione e ruolo dell'admin;
- classe attiva e sua revisione monotona CAS (anche ogni aggiornamento classe richiede la revisione attesa);
- chiave numerica `(github, organization_subject, team_subject)`;
- classe, generazione immutabile `created_at` e revisione monotona `updated_at` del mapping.

Le generazioni sono conservate in `external_group_mapping_generations` da ogni percorso di scrittura, inclusa la compatibilità storage preesistente, e devono avanzare oltre il massimo storico. Rename e delete richiedono generazione e revisione attese. Delete/relink con clock costante o arretrato produce una generazione monotona e impedisce ABA; rename concorrenti non possono sovrascriversi. Un team non viene mai riassegnato implicitamente a un'altra classe.

## Onboarding pending

La riconciliazione è consentita soltanto quando:

1. l'utente è attivo e ancora `pending`;
2. esiste esattamente una identità GitHub collegata;
3. la directory restituisce uno snapshot completo, fresco, correlato allo stesso subject numerico e senza duplicati;
4. esiste esattamente un team mappato nello snapshot, ricontrollato atomicamente su tutte le chiavi al commit;
5. la classe mappata è ancora attiva.

La transazione finale verifica nuovamente revisione utente, generazione dell'identità GitHub, generazione e revisione del mapping e revisione classe. Solo allora inserisce la membership `student` e promuove il ruolo interno a `student`. Zero team o più team mappati lasciano l'utente `pending` senza membership parziale. Errori o snapshot incompleti non vengono interpretati come assenza di membership.

## Limiti

- nessuna credenziale GitHub è acquisita o persistita;
- nessuna sincronizzazione periodica o revoca automatica di studenti già approvati;
- nessuna route HTTP o UI amministrativa;
- nessun repository discovery;
- adapter GitHub App reale e mapping GitLab restano follow-up.

# Collegamento account GitHub

## Scopo

`thebitlab_github_oauth.py` collega un account GitHub a un utente TheBitLab già autenticato. Non crea utenti, non assegna ruoli e non mappa team/classi: la sessione TheBitLab autentica la persona, mentre GitHub diventa una `ExternalIdentity(provider="github")` aggiuntiva.

## Vincoli di sicurezza

- `begin_link()` accetta esclusivamente un `HttpAuthContext` già autenticato.
- Il flow one-time è associato a `user_id`, digest della sessione, revisione utente e browser originario.
- State e browser binding sono conservati solo come SHA-256; il verifier PKCE resta soltanto nella memoria bounded del processo.
- Cookie transazionali `__Host-`, `Secure`, `HttpOnly`, `SameSite=Lax` hanno nomi distinti per state, permettendo più schede.
- Il callback consuma il flow prima del token exchange; binding/sessione errati non consumano il flow. Revisione utente e sessione persistita vengono ricontrollate atomicamente al link.
- Authorization, token e user endpoint sono fissati ai valori GitHub canonici; transport HTTPS bounded e no-redirect.
- Access token, authorization code, client secret e verifier non vengono persistiti.
- La risposta token deve dichiarare `token_type=bearer` e l'identità canonica è l'ID numerico signed-64 restituito da `GET /user`; login, nome ed email sono attributi aggiornabili.

## Transazioni identity

`ExternalIdentityLinkService` usa nuovi primitive storage CAS:

- le varianti `*_for_active_session()` richiedono utente attivo, revisione invariata e sessione persistita non revocata né scaduta nella stessa transazione;
- unlink richiede sempre la sessione autenticata, oltre a owner e generazione `linked_at` attesi;
- le tombstone `(provider, subject, linked_at)` impediscono ABA dopo unlink/relink;
- un utente può collegare un solo account per il provider configurato e uno stesso subject non può avere due owner;
- la migrazione v3 mette in quarantena tutti i link legacy ambigui prima di applicare il vincolo unico `(user_id, provider)`.

## Fuori scope

- route concrete e gestione header HTTP;
- credenziali GitHub reali/browser E2E;
- organization/team mapping e membership classi;
- GitHub App installation token e repository discovery;
- rate limiting edge, da progettare insieme alle route pubbliche (#549).

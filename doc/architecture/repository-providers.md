# Repository provider

## Obiettivo

Il repository provider separa il dominio TheBitLab dal sistema concreto usato per ospitare i repository studenti.

La GUI e i service non devono sapere se una classe arriva da directory locali, team GitHub, gruppi GitLab o da un sistema interno futuro. Devono parlare con una porta applicativa stabile.

## Porta applicativa

Il contratto minimo e in `scripts/thebitlab_repository_providers.py`:

- `RepositoryProvider`: interfaccia per elencare e risolvere repository studenti.
- `StudentRepository`: riferimento normalizzato a un repository studente.
- `LocalRepositoryProvider`: adapter iniziale basato su directory locali.

Il parametro `class_ref` e parte della porta per GitHub/GitLab/team/classi, ma il provider locale lo rifiuta finche non esiste una mappa locale classe/studenti. Questo evita di restituire tutti i repository quando il chiamante si aspetta un filtro di classe.

## Dato normalizzato

`StudentRepository` espone:

- `student_id`: identificativo dello studente nel dominio TheBitLab.
- `repo_ref`: riferimento repository normalizzato e mostrabile in UI.
- `provider`: nome provider, per esempio `local`, `github`, `gitlab`.
- `path`: path locale quando disponibile.
- `metadata`: metadati opzionali specifici del provider.

## Strategia incrementale

1. Stabilizzare provider locale e test unitari.
2. Collegare un flusso reale al provider senza cambiare comportamento utente.
3. Aggiungere adapter GitHub minimale dietro la stessa interfaccia.
4. Progettare GitLab e provider interno senza far dipendere GUI e service dai dettagli esterni.

Questa scelta mantiene piccoli i cambiamenti: rete, autenticazione e semantica team restano fuori dal primo passo.

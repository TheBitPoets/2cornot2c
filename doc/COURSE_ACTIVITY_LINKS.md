# Collegamenti activity, UDA e calendario

Il course design non incorpora una copia dell'activity. Ogni UDA puo mantenere una lista `activity_links` che conserva identita e provenienza del file di catalogo:

```json
{
  "id": "uda-4",
  "title": "Funzioni",
  "activity_links": [
    {
      "activity_id": "c-base-funzioni-verifica-001",
      "activity_path": "activities/examples/practical_test_functions.json",
      "title": "Verifica pratica su funzioni e condizioni",
      "kind": "verifica-pratica",
      "role": "verification",
      "scheduled_on": "2026-11-10",
      "due_on": "2026-11-17"
    }
  ]
}
```

## Invarianti

- `activity_path` e relativo al repository, canonico e confinato in `activities/`;
- `role` e `practice` oppure `verification`, indipendentemente dal testo libero `kind` del catalogo;
- `scheduled_on` e `due_on` sono date ISO opzionali; la scadenza non precede la data pianificata;
- ID e path non possono essere duplicati nella stessa UDA, inclusi alias case-insensitive;
- il path e portabile tra POSIX e Windows: device name, caratteri non validi e alias DOS 8.3 sono rifiutati;
- prima del salvataggio il file deve esistere, restare in `activities/` e dichiarare lo stesso `activity_id`;
- i campi sono bounded e lo schema rifiuta chiavi sconosciute;
- i design legacy senza `activity_links` restano validi.

`scripts/course_activity_links.py` e il confine autorevole. Il server lo applica prima di salvare o generare un percorso. `iter_scheduled_activity_links()` produce copie difensive con il contesto anno/UDA per la vista calendario senza trasformare l'activity in un evento proprietario separato.

L'activity originale resta autorevole per consegna, rubriche e correzione; il link conserva soltanto i metadati necessari alla pianificazione. I bundle asset sono pubblicati in directory immutabili identificate dal digest e il JSON activity viene sostituito atomicamente: un arresto durante l'overwrite non modifica il bundle ancora referenziato. Un bundle nuovo dall'esito incerto viene conservato come orphan innocuo invece di rischiare di cancellare asset gia referenziati; la raccolta degli orphan e un'operazione di manutenzione separata. La cancellazione di una bozza e serializzata con i salvataggi dei percorsi e viene bloccata finche un design corrente o archiviato la referenzia. Dopo la cancellazione non e possibile creare un nuovo link pendente perche il salvataggio richiede nuovamente il file autorevole.

La UI deve aggiornare questi metadati in modo esplicito quando il catalogo cambia, evitando modifiche implicite ai percorsi gia approvati.

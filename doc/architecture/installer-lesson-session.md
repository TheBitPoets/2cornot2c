# Supervisore della sessione studente nell'installer

## Stato e perimetro S1

`installer/lesson_session.py` implementa il nucleo del ciclo di vita della
lezione. Non e ancora collegato al menu e non abilita il flusso per gli studenti.
La proposta completa resta in `../PROPOSTA_SESSIONE_STUDENTE.md`.

Il modulo coordina un processo posseduto attraverso un adapter, distingue la
chiusura del processo dalla fine verificata della lezione e impedisce un nuovo
avvio quando esiste una sessione incompleta. Non esegue pairing, salvataggi,
consegne, revoche, apertura browser o cancellazione del lavoro.

## Stato locale e concorrenza

Il chiamante deve fornire una directory di stato stabile, comune a tutti i
launcher della stessa installazione e alle modalita `shared` e `personal`.
Non usare una directory diversa per studente, attivita o avvio. La scelta del
percorso definitivo appartiene all'integrazione Windows, ancora da implementare.

Prima di avviare il processo, il supervisore crea esclusivamente la directory
`active-lesson`. La creazione atomica impedisce due avvii concorrenti anche se
entrambi i launcher erano inizialmente inattivi. `owner.json` contiene soltanto
versione 1, ID casuale locale e modalita del PC; non contiene PID, identita,
URL, credenziali, codici pairing o percorsi dei sorgenti.

La presenza di qualsiasi oggetto `active-lesson`, anche vuoto, malformato o
residuo di un avvio fallito, blocca il nuovo avvio. Il riavvio non legge ne
ripresenta account o lavoro precedenti. Non determina la vita di un processo
da un PID persistito e non recupera automaticamente il marcatore. Il recupero
assistito e un incremento successivo: non rimuovere il marcatore alla cieca.

La modalita e obbligatoria e immutabile durante la lezione. Tutte le chiamate
su una stessa istanza avvengono nel thread del menu; l'esclusione su filesystem
serve invece per istanze/processi diversi. Questo protocollo evita riusi
accidentali, non fornisce isolamento da una persona con lo stesso account OS.
Il modello copre interruzioni del processo; non certifica durabilita del
filesystem dopo perdita di alimentazione o protezione da mutazioni ostili.

## Processo e transizioni

| Evento | Stato risultante | Nuovo avvio/uscita normale |
|---|---|---|
| Nessun marcatore | `idle` | Consentiti |
| Claim e avvio riusciti | `running` | Bloccati |
| Richiesta cooperativa di fine | `stopping` | Bloccati |
| Processo terminato con codice zero | `verifying` | Bloccati |
| Errore/crash, stato ambiguo, marcatore preesistente | `recovery-required` | Bloccati |
| Conferme complete e rilascio marcatore riuscito | `closed` | Consentiti |

`running` indica soltanto il processo monitorato: non prova pairing riuscito o
identita autenticata. `poll()` non attende la fine del processo. L'adapter deve
restituire un handle posseduto, raccogliere il processo terminato e implementare
`request_stop()` come richiesta cooperativa non bloccante. Il supervisore non
chiama kill, terminate o wait e non arresta VM, Docker o editor.

`start(launch)` richiede una funzione di avvio breve che restituisca l'handle;
non avviare pairing/rete inline nel thread del menu. Se l'adapter crea un
processo e poi fallisce, deve conservarne la responsabilita fino alla raccolta:
il supervisore non puo recuperare un handle che non gli e stato restituito.
La console Windows separata e il canale cooperativo verso la TUI sono lavoro S2.

Un errore di richiesta chiusura mantiene l'handle e permette un nuovo tentativo.
Un errore di osservazione conserva l'handle per la raccolta successiva, ma rende
necessario il recupero; una successiva uscita zero non cancella quell'ambiguita.

## Conferme di fine lezione

`ClosureEvidence` e un valore interno in memoria, prodotto da adapter trusted,
non un formato di ricevuta HTTP/JSON. Le conferme devono riguardare l'esatto
`session_id` locale e devono essere booleani `True`, non valori truthy.

L'integrazione futura deve fermare le scritture e poi confermare:

1. conservazione remota di tutto il lavoro corrente, senza outbox pendente,
   conflitti o file modificati dopo la verifica;
2. chiusura cooperativa degli editor/processi gestiti che scrivono;
3. revoca TUI confermata dal server;
4. revoca della sessione web dedicata confermata dal server;
5. chiusura del browser dedicato;
6. sul PC condiviso, rimozione dei soli dati temporanei appartenenti alla
   sessione, esclusivamente dopo la conferma del lavoro da mantenere.

L'adapter deve raccogliere le conferme dopo l'arresto degli scrittori e l'uscita
della TUI; non riutilizzare conferme di una precedente versione dei file.
La sequenza delle operazioni e la validazione delle ricevute sono responsabilita
degli adapter futuri; il nucleo non puo verificare affermazioni inventate dal
chiamante. Codice di uscita zero, invio HTTP riuscito o outbox vuota da soli non
provano il salvataggio di tutte le bozze.

`complete()` accetta le conferme soltanto in `verifying`. Sul PC personale la
rimozione dati non e richiesta; conservazione remota e revoche restano richieste
per dichiarare questa chiusura completa. La futura UX offline puo offrire una
sospensione esplicita, senza chiamarla chiusura verificata.

Il supervisore elimina soltanto il proprio `owner.json` verificato e la
directory vuota, senza cancellazioni ricorsive. Contenuto inatteso o errore I/O
mantengono il blocco. Non tocca mai `student-delivery`, `lab`, `lab2`, profili
browser, installazione o outbox. La cancellazione condivisa dovra essere
implementata e provata separatamente; nessun adapter di pulizia esiste in S1.

## Dipendenze e divisione del lavoro

- S1, questo incremento: supervisore, test autonomi e questo contratto interno.
- S2: adapter Windows/console e arresto cooperativo, browser dedicato temporaneo,
  pairing annullabile e stato identita, integrazione del menu reattivo.
- Consegne/bozze, altra istanza: contratto di salvataggio e ripristino delle bozze,
  ricevuta della versione esatta, conflitti, outbox e insieme dei file coperti.
  Non modificare in questa linea `scripts/student_delivery_*`,
  `scripts/student_lab_*` o i contratti storage/grading senza coordinamento.
- S3 dopo integrazione: fine lezione completa, pulizia circoscritta, recupero
  assistito e prova di cambio studente A/B sullo stesso account Windows.

Non assumere un endpoint bozze o ricavare la conferma da una consegna finale.
Salvare il lavoro non deve creare implicitamente uno snapshot valutabile.
I percorsi restano quelli esistenti, con `student-delivery` nella root.
La TUI corrente apre il browser ordinario e il suo exit code non attesta questa
sequenza: non collegarla direttamente al menu come flusso condiviso completo.

Riferimenti: [pairing TUI](tui-pairing-cli.md),
[sessione web](web-session-http-routes.md),
[storage consegne](student-delivery-storage.md),
[grading](student-delivery-grading.md).

## Verifiche

`python -m pytest tests/test_installer_lesson_session.py` copre concorrenza,
marcatori incompleti, errori di avvio e arresto, uscita zero/nonzero, conferme
mancanti o di altra sessione, modalita condivisa/personale e conservazione dei
file. Include un processo Python reale chiuso cooperativamente via pipe e
raccolto con timeout, senza browser, servizi reali o credenziali.

Restano necessarie le prove degli adapter e le prove reali Windows/browser,
rete/offline, VM/Docker, percorsi con spazi e cambio studente prima del rilascio.

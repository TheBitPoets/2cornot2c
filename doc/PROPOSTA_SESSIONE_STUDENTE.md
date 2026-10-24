# Proposta: sessione studente da scuola e da casa

Stato: requisiti consolidati il 24 settembre 2026; implementazione successivamente autorizzata. Primo incremento S1: nucleo del supervisore in `installer/lesson_session.py`, ancora senza collegamento al menu. Le funzioni complete descritte qui non sono gia disponibili. Per perimetro implementato, dipendenze e verifiche vedere [il contratto S1](architecture/installer-lesson-session.md).

## Obiettivo e scelte consolidate

- Avvio senza comandi dall'interfaccia Ambiente 2cornot2c, mantenendo il menu utilizzabile per aprire VM o Docker mentre la TUI consegne e aperta.
- A scuola piu studenti/classi condividono lo stesso account Windows Alunno. Supportare anche casa distinguendo PC condiviso da PC personale, con impostazione esplicita.
- Google autentica lo studente; pairing browser per ciascuna esecuzione della TUI, senza credenziali TUI persistenti. Account pending richiede abilitazione del docente/amministratore.
- Bozze da salvare e recuperare attraverso TheBitLab; GitHub non e richiesto nel flusso iniziale. Salvataggio bozza e consegna finale sono azioni distinte. Continuita tra dispositivi e gestione versioni concorrenti devono essere implementate e verificate.
- Conservare <clone>/student-delivery e struttura interna per workspace/revisione/attivita. Nessun trasferimento in lab/lab2 e nessun collegamento simbolico necessario. lab e lab2 restano invariati.

## Interfaccia e flusso

1. Menu principale: Inizia la lezione - associa e apri la TUI; Termina la lezione; funzioni attuali Avvia ambiente, Installa/completa/ripara, Aggiorna, Disinstalla selettivamente, Ripristina PC, Esci. Indicazione della modalita e dello stato sessione. Chiusura sessione disabilitata se assente; niente doppio avvio TUI.
2. Avvio: controllo prerequisiti, codice pairing visibile e scadenza, browser dedicato con profilo temporaneo; istruzione di accedere con la propria email autorizzata, verificare identita, non salvare password. Riapri pagina, annulla, rinnova codice scaduto. Conferma identita nel browser. Gestire account errato/pending e apertura browser fallita.
3. Autorizzazione riuscita: TUI consegne in finestra separata con nome studente visibile; processo monitorato dal menu. Menu principale resta reattivo. Avvio VM/Docker possibile prima o dopo la TUI.
4. Selezione attivita: recuperare materiali e bozza remota disponibile, proteggere eventuali modifiche locali concorrenti. Mostrare stato salvataggio. Apri cartella e Apri nell'ambiente (VM/Docker) devono usare il percorso reale dell'attivita, senza richiedere navigazione manuale negli hash.
5. Salva il lavoro conserva una bozza; Consegna al docente richiede azione esplicita e ricevuta/snapshot secondo i contratti esistenti. Nessuna consegna finale implicita alla chiusura.
6. Termina lezione da menu o TUI: coordinare salvataggi/editor/processi gestiti, verificare persistenza remota del lavoro, revocare sessione TUI, terminare sessione web/profilo browser dedicati. Non chiudere forzatamente VM, Docker o editor con dati non salvati. Esci dal menu con sessione aperta deve gestirla esplicitamente.
7. PC condiviso: rimuovere soltanto copie temporanee della sessione, dopo salvataggio verificato; non toccare lab/lab2, installazione o altri file/account/browser. PC personale: conservare lavoro locale. Non promettere logout Google globale.
8. Offline, errore invio o revoca: stato incompleto esplicito; non dichiarare PC pronto e non cancellare lavoro pendente. Su PC personale conservare lavoro per invio successivo; su condiviso coinvolgere docente. Dopo crash rilevare sessione interrotta senza ripresentare automaticamente account/lavoro precedente.

## Percorsi verificati nei sorgenti

| Windows | VM | Docker avviato dal menu |
|---|---|---|
| <clone>/lab | /lab | /workspace/lab |
| <clone>/lab2 | /lab2 | /workspace/lab2 |
| <clone>/student-delivery | /vagrant/student-delivery (atteso, da provare) | /workspace/student-delivery |

Vagrantfile:178-179 condivide lab/lab2. La disabilitazione di /vagrant e commentata alla riga 185; Vagrant condivide di default il progetto in /vagrant. Nessuna verifica sulla VM installata: verificare prima di aggiungere configurazione. Il launcher Windows parte nella root del clone e avvia student_dev_shell.py, il cui default monta la directory corrente in /workspace.

Con delivery_api=true, student_delivery_client.prepare_workspace crea <root>/student-delivery/<chiave>/<activity_digest>/assignments/<activity_id> e conserva file esistenti. Senza API consegne, il flusso legacy usa workspace gia predisposti. Il download materiali esistente non equivale a sincronizzazione delle bozze tra dispositivi.

## Limiti e verifiche richieste prima del rilascio

- Browser supportati, gestione profilo temporaneo, revoca coordinata e recupero sessione interrotta.
- Salvataggio/ripristino bozze, ricevute, perdita rete, modifiche concorrenti scuola/casa e file ancora aperti negli editor.
- Accesso in lettura/scrittura agli stessi sorgenti da Windows, VM e Docker, con percorsi contenenti spazi; menu reattivo e processi senza duplicati/orfani.
- Cambio studente A/B sullo stesso account, nessun riutilizzo involontario di sessioni o file; nessuna cancellazione con invii pendenti.
- Cartelle/profili sotto lo stesso account Windows non forniscono isolamento di sicurezza tra persone; il progetto mira a evitare riuso accidentale e gestire la pulizia.
- Test proporzionati e prove reali di VM/Docker richiesti all'implementazione. Questa fase ha eseguito soltanto analisi statica; nessun codice modificato.

Riferimenti: architecture/tui-pairing-cli.md, architecture/web-session-http-routes.md, architecture/student-delivery-storage.md, architecture/student-delivery-grading.md, installer/README.md; https://developer.hashicorp.com/vagrant/docs/synced-folders .

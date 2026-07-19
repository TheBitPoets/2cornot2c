# Scenari di test manuali GUI

Questa checklist raccoglie gli scenari manuali da ripetere quando si toccano dashboard docente, dashboard studente, calendario o flusso lab. Serve a riprodurre le prove fatte a mano in modo sempre uguale: stessi dati, stessi URL, stessi risultati attesi.

## Setup comune

Esegui i comandi dalla root del repository.

Gli scenari possono essere eseguiti singolarmente oppure in sequenza. Nell'esecuzione sequenziale lascia
attivo il server tra due scenari consecutivi, salvo quando un passaggio chiede esplicitamente di fermarlo
per cambiare root dati o configurazione. Nell'esecuzione singola applica prima il setup indicato dallo
scenario o, se non presente, questo setup comune.

Se la porta `8765` e gia occupata su Windows:

```powershell
Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess,State
Stop-Process -Id <PID> -Force
```

Prepara la root demo pulita:

```powershell
python scripts/student_lab_demo_setup.py
```

Avvia il server sulla root demo:

```powershell
python scripts/course_board_server.py --root tmp/student-lab-demo
```

Il server stampa le credenziali temporanee della dashboard. Al primo accesso nel browser inserisci l'utente
`teacher` e usa come password il token stampato; le stesse credenziali valgono per tutte le pagine web della demo.

URL principali:

- Dashboard docente consegne: `http://localhost:8765/tools/assignment_dashboard.html`
- Dashboard studente: `http://localhost:8765/tools/student_dashboard.html`
- Percorso docente: `http://localhost:8765/tools/course_board.html`
- Calendario docente: `http://localhost:8765/tools/school_calendar.html`

Dati demo principali:

- Studente: `rossi-mario`
- Activity: `python-demo-somma-001`
- Titolo activity: `Demo somma in Python`
- Classe: `3A-TPSI`
- Etichetta classe: `3A TPSI`
- Team GitHub: `team-3a-tpsi`
- Registro docente: `demo/python-demo-somma-001.json`

## Copertura manuale richiesta

Ogni pannello, modal, vista e comando deve avere almeno uno scenario manuale. Quando una voce cambia, aggiorna la riga corrispondente prima della review della PR.

| Area | Elemento | Scenario minimo | Automatizzabile |
| --- | --- | --- | --- |
| Dashboard docente | Genera registro / crea registro consegne | Seleziona activity, classe o assegnazione, crea registro e verifica feedback visibile | Playwright o Selenium |
| Dashboard docente | Registro selezionato | Carica `demo/python-demo-somma-001.json`, ricarica e verifica riepilogo | Playwright o Selenium |
| Dashboard docente | Studenti | Verifica riepiloghi, filtri attivi, righe studente e modal studenti | Playwright o Selenium |
| Dashboard docente | Quadro classe | Verifica viste `Elenco` e `Matrice`, filtri, bottoni consegna e righe compatte | Playwright o Selenium |
| Dashboard docente | Copertura registri | Verifica stato copertura, filtri e celle dense con nomi lunghi | Playwright o Selenium |
| Dashboard docente | Activity / wizard assegnazione | Crea o modifica activity, genera proposta AI, revisiona, assegna target e salva | Playwright o Selenium con mock API |
| Dashboard docente | Modal dettaglio consegna | Apri una consegna disponibile e verifica link/file/stato | Playwright o Selenium |
| Dashboard docente | Modal dettaglio errori | Usa un report fallito e verifica testo lungo leggibile | Playwright o Selenium |
| Dashboard docente | Modal AI feedback | Verifica approva, respingi, riapri bozza e persistenza dopo ricarica | Playwright o Selenium con API locale |
| Dashboard docente | Modal elenco/matrice | Apri modal grandi e verifica header, filtri, scroll e legenda | Playwright o Selenium |
| Dashboard studente | Riepilogo studente | Seleziona `rossi-mario` e verifica dati personali/lettura sola | Playwright o Selenium |
| Dashboard studente | Consegne | Verifica lista, badge prossima scadenza, mancanti e dettaglio consegna | Playwright o Selenium |
| Dashboard studente | Lab | Verifica workspace, report, test, ultimo tentativo e aiuti | Playwright o Selenium |
| Dashboard studente | Percorso | Verifica percorsi associati, UDA e link ai paragrafi GitHub | Playwright o Selenium |
| Dashboard studente | Calendario | Verifica mese/settimana/anno, lista/calendario, filtri, interruzioni e consegne | Playwright o Selenium |
| Percorso docente | Pannelli percorso/UDA/paragrafi | Verifica creazione/modifica contenuti e collegamenti | Playwright o Selenium |
| Calendario docente | Vista calendario | Verifica modalita, frecce, filtri, UDA programmate/reali e interruzioni | Playwright o Selenium |
| TUI studente | Lista consegne | Avvia TUI e verifica legenda, colori opzionali, date compatte e selezione numerica | Test interattivo o snapshot terminale |
| TUI studente | Dettaglio consegna | Apri una consegna e verifica sezioni, divisori, guida rapida e comandi | Test interattivo o snapshot terminale |
| TUI studente | Comando `e` | Esegui test e salva report, poi verifica GUI studente/docente | Test interattivo piu assert su file |
| TUI studente | Comando `a` | Chiedi aiuto, verifica guida locale e storico, annulla con `b`/invio, valida input non valido | Test interattivo con input finto |
| TUI studente | Comando `h` | Mostra storico aiuti e torna alla consegna | Test interattivo con input finto |
| TUI studente | Comando `o` | Apre workspace se presente, mostra errore chiaro se assente | Test con mock apertura |
| TUI studente | Comandi `b`, `r`, `q` | Torna indietro, ricarica, esce senza perdere stato | Test interattivo con input finto |

Per l'automazione futura, la scelta piu naturale per le GUI web e Playwright, perche gestisce bene browser reali, screenshot e test responsive. Selenium resta possibile se vogliamo uno stack piu tradizionale. Per la TUI conviene partire da test con input finto e snapshot testuali, poi eventualmente passare a un harness terminale piu ricco.

I test GUI automatici vanno introdotti quando i punti di aggancio della UI sono abbastanza stabili, usando attributi espliciti come `data-testid` invece di selettori fragili basati sulla posizione. I test piu pesanti, soprattutto quelli con browser, screenshot, responsive e dati demo end-to-end, sono candidati per una suite notturna o manuale da lanciare quando la macchina non serve per lavorare.

## Collaudo completo con dati durevoli

Quando il flusso activity, assegnazione, consegna, lab e registro sara completo, eseguire tutti gli scenari di questo documento partendo da una root ricreata da zero. Non riutilizzare registri copiati da root temporanee di test: i riferimenti ai workspace devono appartenere alla root demo corrente.

1. Arresta il server che usa `tmp/student-lab-demo`.
2. Esegui `python scripts/student_lab_demo_setup.py` per ricreare dati coerenti e ripetibili.
3. Avvia nuovamente il server con `--root tmp/student-lab-demo`.
4. Esegui nell'ordine gli scenari TUI, dashboard studente e dashboard docente.
5. Verifica non soltanto la visibilita in GUI, ma anche che file, assegnazioni, report, aiuti e cancellazioni siano realmente persistiti o rimossi nella root dati.

## Scenario 1 - Dashboard studente con report riuscito

Obiettivo: verificare che lo studente veda consegna, workspace, report, test e aiuti.

1. Apri `http://localhost:8765/tools/student_dashboard.html`.
2. Seleziona lo studente `rossi-mario`.
3. Controlla che sia visibile la consegna `Demo somma in Python`.
4. Apri il dettaglio della consegna, se presente il bottone di dettaglio.
5. Controlla il pannello `Lab`.

Risultato atteso:

- La consegna `Demo somma in Python` e visibile.
- Il workspace risulta presente.
- Il report risulta presente.
- I test risultano passati: `2/2`.
- L'ultimo tentativo e valorizzato.
- Gli aiuti tracciati sono valorizzati.
- Il feedback AI non approvato dal docente non viene mostrato allo studente come feedback definitivo.

## Scenario 2 - Dashboard docente con registro demo

Obiettivo: verificare che il docente possa caricare il registro generato dalla demo lab.

1. Apri `http://localhost:8765/tools/assignment_dashboard.html`.
2. Nel pannello del registro seleziona `demo/python-demo-somma-001.json`.
3. Clicca `Carica registro`.
4. Controlla i riepiloghi del registro selezionato.
5. Apri il pannello `Studenti`.
6. Apri il modal degli studenti, se disponibile.
7. Nella riga di `rossi-mario`, clicca `Apri consegna`.
8. Seleziona `main.py` e poi `test_main.py` dalla lista dei file.

Risultato atteso:

- Il registro caricato mostra activity `Demo somma in Python`.
- Classe e team sono coerenti con `3A-TPSI` e `team-3a-tpsi`.
- Lo studente `rossi-mario` e presente.
- Lo stato consegna indica una consegna disponibile e tracciata.
- I test risultano `2/2`.
- Il backend report risulta locale.
- Le richieste di aiuto risultano visibili nel riepilogo docente.
- Il modal della consegna mostra il contenuto di `main.py` e `test_main.py` senza errori 404.
- I file aperti appartengono alla root demo corrente, non a una precedente cartella temporanea.

## Scenario 3 - Quadro classe ed elenco consegne

Obiettivo: verificare che il quadro classe rimanga leggibile e che i bottoni aprano la consegna corretta.

1. Apri `http://localhost:8765/tools/assignment_dashboard.html`.
2. Carica il registro `demo/python-demo-somma-001.json`.
3. Nel pannello `Quadro classe` controlla i filtri attivi.
4. Apri la vista `Elenco`.
5. Cerca la riga dello studente `rossi-mario`.
6. Usa il bottone `Consegna`, se abilitato.

Risultato atteso:

- Il filtro classe e coerente con il registro caricato.
- La riga resta compatta e non rompe l'altezza della tabella.
- Il bottone `Consegna` apre la consegna dello studente, non il registro generale.
- Se una consegna non ha link disponibile, il bottone resta disabilitato e la mancanza e indicata chiaramente.

## Scenario 4 - Richieste di aiuto visibili al docente

Obiettivo: verificare che il docente veda quante volte lo studente ha chiesto aiuto e il prompt inviato.

1. Apri `http://localhost:8765/tools/assignment_dashboard.html`.
2. Carica il registro `demo/python-demo-somma-001.json`.
3. Apri il pannello o modal `Studenti`.
4. Cerca `rossi-mario`.
5. Controlla il riepilogo dedicato agli aiuti.
6. Clicca `Dettagli aiuti`.
7. Leggi prompt, risposta, provider, stato e utilizzo dichiarato.
8. Controlla `Token AI dichiarati` nella cella, nel modal e nel riepilogo Studenti.
9. Chiudi il modal e verifica di tornare alla stessa vista Studenti.

Risultato atteso:

- Il docente vede `Aiuti 1`.
- Il docente vede `Aiuti AI 1`.
- La cella resta compatta e non mostra direttamente i prompt lunghi.
- `Dettagli aiuti` apre un modal dedicato.
- Il prompt demo è visibile nel modal: `Puoi darmi un suggerimento senza scrivere la soluzione?`.
- La risposta e il provider sono leggibili senza scorrimento orizzontale.
- Il totale `Token AI dichiarati` coincide con la somma dei contatori mostrati nelle richieste AI.
- Il riepilogo `AI senza contatori` coincide con gli avvisi presenti nelle righe studente.
- Eventuali risposte remote senza usage sono indicate come `Senza contatori` e non aumentano il totale.
- Gli aiuti bloccati sono `0`.

## Scenario 5 - Dettaglio errori test in modal

Obiettivo: verificare che un report fallito mostri gli errori in un modal leggibile, non in una linguetta troppo stretta.

Prepara un errore intenzionale dopo il setup comune:

```powershell
$source = "tmp\student-lab-demo\examples\assignment_tracking\student_repos\rossi-mario\assignments\python-demo-somma-001\main.py"
Set-Content -Path $source -Encoding utf8 -Value @("def somma(a, b):", "    return a - b")
python scripts/student_lab_runner.py --root tmp/student-lab-demo --student-id rossi-mario --activity-id python-demo-somma-001 --write-report
python -m scripts.track_assignments --activity tmp\student-lab-demo\activities\python-demo-somma-001.json --target tmp\student-lab-demo\examples\assignment_tracking\student_repos\rossi-mario --assigned-at 2026-10-12T09:00:00+02:00 --due-at 2026-10-19T23:59:00+02:00 --now 2026-10-18T18:30:00+02:00 --class-id 3A-TPSI --class-label "3A TPSI" --github-team team-3a-tpsi --output tmp\student-lab-demo\teacher-reports\demo\python-demo-somma-001.json
```

Poi:

1. Apri `http://localhost:8765/tools/assignment_dashboard.html`.
2. Carica o ricarica `demo/python-demo-somma-001.json`.
3. Apri `Studenti`.
4. Cerca `rossi-mario`.
5. Clicca `Dettaglio errori`.

Risultato atteso:

- I test risultano falliti, per esempio `0/2`.
- Il bottone `Dettaglio errori` e visibile.
- Il dettaglio si apre in un modal.
- Il testo dell'errore Python o pytest e leggibile anche se lungo.
- Chiudendo il modal si torna alla stessa vista del registro.

Per tornare alla demo pulita:

1. Nel terminale in cui e in esecuzione il server premi `Ctrl+C` e attendi che il processo termini.
2. Rigenera i dati della demo:

```powershell
python scripts/student_lab_demo_setup.py
```

3. Riavvia il server sulla root rigenerata:

```powershell
python scripts/course_board_server.py --root tmp/student-lab-demo
```

4. Ricarica la dashboard nel browser prima di continuare con gli scenari successivi.

## Scenario 6 - Dashboard studente dopo esecuzione TUI

Obiettivo: verificare che un'azione fatta dalla TUI venga riflessa nella GUI studente.

1. Avvia la TUI:

   ```powershell
   python scripts/student_lab_cli.py --root tmp/student-lab-demo --student-id rossi-mario
   ```

2. Seleziona la consegna `Demo somma in Python`.
3. Esegui il runner con il comando indicato dalla TUI.
4. Esci dalla TUI.
5. Apri `http://localhost:8765/tools/student_dashboard.html`.
6. Seleziona `rossi-mario`.

Risultato atteso:

- La dashboard studente vede lo stesso report prodotto dalla TUI.
- Workspace, report, test e ultimo tentativo sono coerenti.
- Le richieste di aiuto registrate dalla TUI compaiono nella dashboard.

## Scenario 7 - Comandi TUI studente

Obiettivo: verificare che la TUI sia comprensibile, robusta sugli input e coerente con dashboard e report.

1. Se stai continuando dagli scenari precedenti, ferma con `Ctrl+C` il server avviato durante il setup
   comune. Prepara quindi di nuovo la demo e avvia il server docente con provider Codex:

   ```powershell
   python scripts/student_lab_demo_setup.py
   $env:THEBITLAB_STUDENT_HELP_PROVIDER="codex"
   $env:THEBITLAB_STUDENT_HELP_SECRET="demo-only-student-help-secret-change-me"
   python scripts/student_help_auth.py --student-id rossi-mario
   python scripts/course_board_server.py --root tmp/student-lab-demo
   ```

   Conserva il token studente stampato da `student_help_auth.py` per il passo successivo. Il server stampa
   separatamente il token dashboard docente: non usarlo nella TUI e non condividerlo con gli studenti.

2. In un secondo terminale avvia la TUI sulla stessa root:

   ```powershell
   $env:THEBITLAB_STUDENT_HELP_TOKEN="<token studente stampato da student_help_auth.py>"
   python scripts/student_lab_cli.py --root tmp/student-lab-demo --student-id rossi-mario --server-url http://127.0.0.1:8765
   ```

3. Nella lista iniziale controlla legenda, date compatte e stati.
4. Premi un valore non valido, per esempio `x`.
5. Seleziona la consegna con il numero.
6. Nel dettaglio controlla guida rapida, sezioni e divisori.
7. Premi `h`, leggi lo storico aiuti e torna indietro.
8. Premi `a`, poi `b`: la richiesta deve essere annullata.
9. Premi `a`, poi invio senza testo: la richiesta deve essere annullata.
10. Premi `a`, poi un tipo diverso da `1`, `2`, `3`, `b` o invio: deve comparire errore.
11. Premi `a`, scegli `3`, scrivi un prompt e invia la richiesta.
12. Controlla che l'esito immediato sia diviso da linee tratteggiate e mostri tipo, stato e risposta a capo. Con Codex operativo deve comparire `Codex locale (macchina docente)`.
13. Ferma il server, imposta `THEBITLAB_STUDENT_HELP_PROVIDER=local`, riavvialo e ripeti: deve comparire `Guida locale (nessuna AI esterna)`.
14. Premi `h` e verifica che prompt e risposta siano entrambi nello storico.
15. Ripeti con un URL o un identificatore lungo senza spazi e verifica che venga mandato a capo senza scorrimento orizzontale.
16. Premi `e` per eseguire test e salvare report.
17. Premi `b` per tornare alla lista.
18. Premi `r` per ricaricare.
19. Premi `q` per uscire.

Risultato atteso:

- Gli input non validi non eseguono azioni.
- `b` e invio annullano o tornano indietro dove previsto.
- Dopo un comando nel dettaglio si resta nel dettaglio della consegna, non si torna alla lista generale.
- Codex locale e la guida di fallback sono distinti dall'etichetta del provider e non mostrano una soluzione completa.
- La TUI segnala chiaramente quando il server non è raggiungibile e non salva direttamente l'evento sul client.
- L'esito immediato non ripete la motivazione della policy quando la richiesta riesce; per richieste bloccate o errori mostra subito il motivo.
- Prompt e risposta restano visibili nello storico della consegna.
- Ogni richiesta nello storico è separata da linee tratteggiate e prompt, risposta, motivo ed esito sono distinguibili per colore.
- Con `--no-color` la stessa gerarchia resta leggibile grazie a intestazioni, rientri e separatori.
- Il report salvato dalla TUI viene letto dalla dashboard studente.
- Le richieste di aiuto salvate dalla TUI vengono viste dal docente.
- Gli accenti e i testi italiani sono corretti.

## Scenario 8 - Percorso e calendario studente

Obiettivo: verificare che la vista studente mostri il percorso associato e il calendario in sola lettura.

1. Apri `http://localhost:8765/tools/student_dashboard.html`.
2. Seleziona `rossi-mario`.
3. Controlla il pannello del percorso.
4. Passa alla vista calendario, se disponibile.
5. Prova i filtri di visualizzazione.
6. Prova la vista lista e la vista calendario.

Risultato atteso:

- Lo studente vede solo percorsi associati al suo profilo o alla sua classe.
- I paragrafi del percorso sono cliccabili e puntano alla pagina GitHub con ancora del paragrafo.
- Il calendario e in sola lettura.
- Consegne, UDA reali, UDA programmate e interruzioni sono distinguibili.
- Le interruzioni usano lo sfondo a strisce salmone/bianco.

## Scenario 9 - Percorso docente

Obiettivo: verificare creazione, modifica, persistenza, protezione dagli errori e accessibilità della pagina Percorso.

1. Ferma con `Ctrl+C` il server dello Scenario 7, se ancora attivo. Avvia quindi il server senza root demo,
   usando i dati del repository:

   ```powershell
   python scripts/course_board_server.py
   ```

2. Apri `http://localhost:8765/tools/course_board.html` e autenticati con le credenziali stampate dal server.
3. Usa `Nuovo progetto` e crea `test-manuale-percorso.json`.
4. Aggiungi un percorso con settimane e ore valide. Prova poi a crearne uno con `0` settimane e verifica il bordo rosso e il messaggio di errore.
5. Nel catalogo a sinistra usa il pulsante `+` su un paragrafo, poi premilo di nuovo sullo stesso paragrafo.
6. Modifica una cornice e premi `Ricarica`: annulla la conferma e verifica che la modifica resti visibile; ripeti accettando e verifica che torni l'ultimo stato salvato.
7. Usa `Salva progetto con nome` indicando di nuovo `test-manuale-percorso.json`: annulla la richiesta di sovrascrittura e verifica che l'archivio precedente non cambi.
8. Salva regolarmente il progetto. Se il provider AI è configurato, genera una sola cornice, avvia una nuova coda e usa `Annulla`; verifica che testo e indicatori di qualità tornino allo stato iniziale.
9. Usa soltanto la tastiera per raggiungere il catalogo e aggiungere un paragrafo con il pulsante `+`.
10. Restringi la finestra a circa `390 px`: pannelli, titoli, campi e pulsanti devono restare leggibili senza sovrapporsi.
11. Cancella `test-manuale-percorso.json` dalla board per ripulire i dati di prova.

Risultato atteso:

- I dati non validi non entrano nel progetto.
- Lo stesso paragrafo non viene duplicato nello stesso percorso.
- Ricarica e navigazione non scartano modifiche senza conferma.
- Un nome già esistente richiede conferma prima della sovrascrittura.
- L'annullamento AI ripristina sia il testo sia gli indicatori di qualità.
- I comandi essenziali sono raggiungibili da tastiera e restano usabili su mobile.

## Scenario 10 - Calendario docente

Obiettivo: verificare che il calendario docente resti coerente con il percorso e con la dashboard studente.

1. Con il server dello Scenario 9 ancora attivo, apri `http://localhost:8765/tools/school_calendar.html`.
2. Prova modalità `settimana`, `mese` e `anno`.
3. Prova frecce avanti/indietro e filtri visibili.

Risultato atteso:

- La grafica resta coerente con lo stile morbido del calendario docente.
- I filtri non nascondono dati senza indicarlo.
- Le UDA reali e programmate sono distinguibili quando presenti.
- Le interruzioni sono visibili e non si confondono con consegne mancanti.

## Template per nuovi scenari

Usa questo formato quando aggiungi una prova manuale:

```text
## Scenario N - Titolo

Obiettivo:

Prerequisiti:

Passi:
1. ...
2. ...

Dati da selezionare:

Risultato atteso:

Regressioni da controllare:
```

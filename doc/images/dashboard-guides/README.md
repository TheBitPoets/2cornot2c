# Screenshot guide dashboard

Questa cartella conterra gli screenshot usati dalle guide operative:

- [`../../DASHBOARD_DOCENTE_GUIDA.md`](../../DASHBOARD_DOCENTE_GUIDA.md)
- [`../../DASHBOARD_STUDENTE_GUIDA.md`](../../DASHBOARD_STUDENTE_GUIDA.md)

Per ora e una checklist: gli screenshot sono **da fare**.

## Regole di cattura

1. Avviare sempre il server locale:

   ```bash
   python scripts/course_board_server.py
   ```

2. Aprire le pagine tramite `http://localhost:8765/...`, non come file locali.
3. Usare dati demo coerenti e ripetibili.
4. Preferire viewport desktop per i flussi docente e almeno uno screenshot mobile per la vista studente.
5. Prima di catturare, controllare che:
   - non ci siano errori visibili;
   - il pannello o modal descritto sia aperto;
   - filtri, select e riepiloghi mostrino dati significativi;
   - non siano visibili token, path personali non necessari o dati sensibili.
6. Aggiornare lo stato da `da fare` a `fatto` quando l'immagine viene salvata.

## Dati demo consigliati

Pagina docente:

- URL: `http://localhost:8765/tools/assignment_dashboard.html`
- Roster: `doc/classes/demo-3a.json`
- Activity: una activity demo disponibile nella select **Activity salvate**
- Registro: un registro demo in `teacher-reports/demo` o `teacher-reports/demo-3a`

Pagina studente:

- URL: `http://localhost:8765/tools/student_dashboard.html`
- Classe: roster demo disponibile nella select **Classe**
- Studente: uno studente demo con consegne visibili, preferibilmente con almeno un feedback approvato

## Screenshot docente

| File | Stato | Pagina | Cosa deve mostrare |
|---|---|---|---|
| `docente-genera-registro.png` | da fare | Dashboard docente | Pannello **Genera registro** con activity, roster, output registro, scadenza e target studenti visibili |
| `docente-roster-classe.png` | da fare | Dashboard docente | Pannello **Roster classe** con classe, activity, output registro, studenti attivi, target locali e fallback demo |
| `docente-registro-selezionato.png` | da fare | Dashboard docente | Pannello **Registro selezionato** con registro caricato e riepilogo compilato |
| `docente-quadro-classe.png` | da fare | Dashboard docente | Pannello **Quadro classe** con riepilogo e bottone per aprire il modal |
| `docente-studenti.png` | da fare | Dashboard docente | Pannello **Studenti** con riepilogo del registro selezionato |
| `docente-copertura-registri.png` | da fare | Dashboard docente | Copertura registri con riepilogo e gruppi activity riconoscibili |
| `docente-revisione-consegna.png` | da fare | Dashboard docente | Modal revisione consegna con lista file a sinistra e contenuto file a destra |

## Scenari docente

| File | Stato | Scenario | Cosa deve mostrare |
|---|---|---|---|
| `scenario-genera-registro-01.png` | da fare | Generazione registro | Activity e roster selezionati prima della generazione |
| `scenario-genera-registro-02.png` | da fare | Generazione registro | Pannello roster classe con target verificabili |
| `scenario-genera-registro-03.png` | da fare | Generazione registro | Registro generato e caricato in **Registro selezionato** |
| `scenario-carica-registro.png` | da fare | Caricare registro | Select registri, registro scelto e riepilogo dopo caricamento |
| `scenario-quadro-classe.png` | da fare | Quadro classe | Modal quadro classe con filtri, elenco o matrice visibili |
| `scenario-revisione-consegna.png` | da fare | Revisione consegna | Modal revisione con file consegnati e contenuto syntax-highlighted |
| `scenario-feedback-ai.png` | da fare | Feedback AI | Stato feedback AI e azioni docente su bozza/approvazione/respinta |

## Screenshot studente

| File | Stato | Pagina | Cosa deve mostrare |
|---|---|---|---|
| `studente-panoramica.png` | da fare | Vista studente | Header, select classe/studente, riepilogo e lista consegne |
| `studente-selezione.png` | da fare | Vista studente | Select **Classe** e **Studente** con dati demo caricati |
| `studente-riepilogo.png` | da fare | Vista studente | Card riepilogo con studente, consegne, consegnate, in ritardo e feedback |
| `studente-consegne.png` | da fare | Vista studente | Lista consegne con stato, scadenza, grading e link |
| `studente-grading.png` | da fare | Vista studente | Dettaglio grading/test visibile in una consegna |
| `studente-feedback.png` | da fare | Vista studente | Feedback approvato visibile allo studente |

## Scenari studente

| File | Stato | Scenario | Cosa deve mostrare |
|---|---|---|---|
| `scenario-studente-demo.png` | da fare | Apertura demo | Classe e studente selezionati, riepilogo non vuoto |
| `scenario-studente-consegna.png` | da fare | Lettura consegna | Una consegna con stato, scadenza e grading leggibili |
| `scenario-studente-feedback.png` | da fare | Feedback approvato | Feedback pubblicato e nessuna bozza AI visibile |

## Dopo aver aggiunto immagini

Quando uno screenshot viene salvato:

1. aggiornare lo stato in questa checklist;
2. verificare che il nome file corrisponda a quello citato nelle guide;
3. controllare dimensione e leggibilita;
4. valutare se inserirlo direttamente nella guida o lasciarlo come riferimento linkato.

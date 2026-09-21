# Audit degli errori di installazione a scuola — 21 settembre 2026

Sono state lette tutte le sette foto nella cartella locale `Desktop/errori`.
Le issue contengono trascrizioni tecniche, riscontri nel codice e criteri di
completamento; le immagini originali non sono state pubblicate.
Il collegamento tra il problema di David e la issue #779 è stato confermato
dal docente. Non è nota la versione del codice eseguita su ciascun PC.

## Copertura delle evidenze

I nomi completi dei file sono `WhatsApp Image 2026-09-21 at <ora>.jpeg`.

| Foto | Evidenza e interpretazione | Issue |
|---|---|---|
| 08.32.52, 08.33.20 | WSL non installato; Docker CLI, motore e immagine con `FileNotFoundError`. È una diagnosi di prerequisiti mancanti, non la prova di tre installazioni fallite. Mancano istruzioni utili e controlli consapevoli delle dipendenze. | [#782](https://github.com/TheBitPoets/2cornot2c/issues/782) |
| 08.37.58 | E09 su Python 3.12, WinHTTP 12002 / `0x80072ee2`, exit `-2147012894`. Il pacchetto è trovato nella sorgente winget, ma il comando chiede `--source`. La sorgente in timeout non è visibile. | [#779](https://github.com/TheBitPoets/2cornot2c/issues/779), nuova evidenza aggiunta |
| 08.40.32 | E20 WSL; il dettaglio conserva soltanto `FullyQualifiedErrorId` / `WriteErrorException`. Causa WSL non determinabile: il sistema perde l'errore utile del processo elevato. | [#783](https://github.com/TheBitPoets/2cornot2c/issues/783) |
| 08.54.59 | Script non trovato, refuso `stundet_lab_cli.py`, directory con la sola `.git`. Il refuso è presente, ma non spiega l'assenza della cartella scripts. Checkout incompleto/non ancora disponibile è l'evidenza; origine non accertata. | [#784](https://github.com/TheBitPoets/2cornot2c/issues/784) |
| 08.59.30, primo tentativo | Anche con `student_lab_cli.py` corretto, file assente. Non è noto se sia lo stesso PC della foto precedente. | [#784](https://github.com/TheBitPoets/2cornot2c/issues/784) |
| 08.59.30, secondo tentativo | Il client parte e risponde «Il server pairing ha restituito una risposta non valida». Lo stesso messaggio copre schema/campi incompatibili e scadenza incoerente con l'orologio locale. Non è possibile scegliere una causa dalla foto. | [#785](https://github.com/TheBitPoets/2cornot2c/issues/785) |
| 09.00.18 | E25, ma i dettagli indicano una VM Bento legacy. Il blocco protegge la VM esistente; titolo «box non disponibile» e suggerimento di controllare Internet non spiegano il recupero corretto. | [#786](https://github.com/TheBitPoets/2cornot2c/issues/786) |

Cinque nuove issue e una issue esistente aggiornata coprono tutte le foto.
Il timeout Python e il certificato di David restano distinti come sintomi,
ma condividono la correzione della scelta esplicita della sorgente, già in #779.
La foto del timeout non dimostra che la sorgente guasta fosse msstore.

## Riscontri tecnici

Codice di riferimento dell'audit: `de6bdf3862768e6601e5cbd8cccea138c8fca0d5`
(contenuti poi inclusi nel merge #781).

- `installer/diagnostics.py::diagnose` usa il nome dell'eccezione per comandi
  assenti/timeout; `run_check` trattiene la prima riga e 160 caratteri.
  `installer/tui.py::refresh_report` applica messaggi guidati a risorse/rete.
- `scripts/prepare-wsl-windows.ps1` non trasferisce strutturalmente stdout/stderr
  del figlio elevato; `installer/executor.py::execute_plan` trattiene soltanto
  l'ultima riga dell'output (300 caratteri). Questa catena spiega la diagnosi E20
  insufficiente, non la causa originaria del fallimento di WSL.
- `scripts/bootstrap-classroom-windows.ps1` sceglie aggiornamento in base alla
  presenza di `.git`, senza una verifica esplicita dei file applicativi minimi.
- `scripts/thebitlab_tui_pairing_client.py::begin` rifiuta schema/campi o durata
  non conformi con il medesimo messaggio; confronta la scadenza con l'UTC locale,
  con massimo 15 minuti. Il codice corrente usa già `TheBitLab-TUI/1.0`.
  #681 e #682 sono chiuse e riguardano lo smoke staging: non dimostrano che
  l'errore attuale sia causato da Cloudflare.
- `installer/classroom_images.py::install_image` rifiuta la sostituzione delle
  VM legacy. La migrazione esiste già, con conferma `RICREA VM`; #621 e #641
  sono chiuse. #786 chiede una diagnosi e un percorso assistito migliori,
  preservando tale protezione.

## Correzione locale di #779

Il bootstrap usava install/upgrade winget senza selezione della sorgente.
Questo permetteva a msstore guasta di bloccare Git disponibile in winget.
La foto Python mostra anche un timeout con richiesta esplicita di `--source`.

La modifica locale seleziona `--source winget` per Git, Python 3.12 e micro
nel bootstrap e per Git, Vagrant, VirtualBox e Docker Desktop nei piani TUI.
E09 distingue certificato `0x8a15005e`, timeout `0x80072ee2` e altri fallimenti;
conserva il codice tecnico senza attribuire ogni errore al rifiuto di Windows.
Nessuna modifica alle sorgenti configurate e nessun indebolimento TLS.
La procedura durevole è documentata in `installer/README.md`.

La selezione tramite `--source` è prevista dalla
[documentazione Microsoft di winget install](https://learn.microsoft.com/en-us/windows/package-manager/winget/install).
Il codice 12002 identifica un timeout secondo la
[documentazione Microsoft WinHTTP](https://learn.microsoft.com/en-us/windows/win32/winhttp/error-messages).
Un timeout reale della sorgente scelta o del download continua correttamente
a bloccare l'installazione: questa modifica non ripara la rete della scuola.

La verifica descritta è **locale**. La prova sul PC di David resta necessaria
prima di considerare risolto il caso reale di #779.

## Correzioni locali di #782–#786

- #782: prerequisiti mancanti spiegati senza eccezioni Python; controlli Docker
  dipendenti sospesi e timeout distinti. Il menu indica come installare/completare.
- #783: resoconto WSL dal processo elevato con fase, codice nativo e output
  limitato; separati annullamento UAC, assenza del resoconto e mancata registrazione
  della ripresa. Log conservato localmente e causa visibile nel menu.
- #784: verifica origine/file essenziali; recupero del checkout con sola `.git`
  tramite conservazione integrale in una cartella sorella e nuovo clone. Origini
  diverse, lock, junction e checkout incompleti con file richiedono assistenza.
  Un download fallito non elimina la copia precedente. Il refuso nel comando
  resta distinto dal problema del checkout.
- #785: P01 distingue contratto/campi non validi; P02 segnala incoerenza fra
  scadenza e orologio. Istruzioni per aggiornamento/sincronizzazione e assistenza,
  senza rilassare validazione e scadenze. Nessun payload o codice nei messaggi
  o nei traceback verificati dai test.
- #786: diagnosi e installazione distinguono legacy E26, stato incoerente E27,
  release inattiva E28 dagli errori generici E25. Migrazione sempre esplicita;
  nessuna VM eliminata automaticamente. Docker resta selezionabile.

Procedure canoniche: `installer/README.md` e
`doc/architecture/tui-pairing-cli.md`. Il disinstallatore con checkbox non è
stato implementato: l'utente ne ha chiesto soltanto la discussione.

## Verifiche e limiti aggiornati

- Test di regressione prima della modifica: un fallimento atteso, con E09
  nonostante Git disponibile nel mock della sorgente winget.
- Installata nella venv di sviluppo la versione uTUI fissata dal repository:
  i test dell'interfaccia non vengono più saltati per dipendenza mancante.
- Suite estesa di 13 moduli: 306 pass, un test preesistente bloccato da Windows
  1314 durante la creazione del symlink. La fixture usa ora una junction quando
  manca quel privilegio: modulo migrazione 14/14 pass, stessa protezione verificata.
- Ultima verifica pairing/CLI: 122 pass, incluse tre ulteriori regressioni sui
  traceback. In totale **310 test distinti verificati con successo** attraverso
  suite estesa e riesecuzioni mirate; nessun errore di test rimasto aperto.
- Test PowerShell eseguono funzioni reali caricate via AST con winget/WSL/UAC
  simulati e repository Git locali. Verificati riavvio/ripresa, errori nativi,
  clone interrotto, rerun, conservazione file, lock, origini diverse e junction.
- I tre nuovi moduli sono inclusi esplicitamente nel job Windows di Quality.
- `git diff --check`: PASS. Nessuna installazione reale, modifica WSL/VM,
  chiamata di pairing o intervento sul server; nessuna prova su PC scolastici.
- WSL richiede il codice/log originario; pairing richiede versione client/server
  e verifica dell'orologio; checkout richiede stato/HEAD del repository; VM
  richiede inventario dei dati prima di qualsiasi migrazione autorizzata.

Prima di far rilanciare il comando agli studenti occorrono integrazione,
review/CI e prova su un PC da 8 GB,
incluso quello di David. Le cause operative di WSL e pairing non sono ricostruibili
dalle sole foto: i nuovi diagnostici servono a identificarle se persistono.
Tutte le issue rimangono aperte fino all'integrazione e alle verifiche richieste.

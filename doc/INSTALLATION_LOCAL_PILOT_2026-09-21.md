# Pilot locale: anteprima disinstallazione selettiva

## Ambito e risultato

Prova autorizzata sulla macchina di sviluppo, senza rimozioni. Non sostituisce
il pilot scolastico Docker su PC da 8 GB o la verifica sul PC di David.
Le correzioni scuola della PR #787 sono integrate in main. La disinstallazione
selettiva è una modifica locale successiva, non ancora pubblicata.

L'anteprima eseguita dal checkout di sviluppo ha individuato l'installazione
in `C:/Users/acari/2cornot2c`, distinta dal checkout di sviluppo:

| Voce | Riscontro dell'anteprima |
|---|---|
| Progetto | Cartella presente |
| VM | Directory di stato presente; non è stato interrogato o avviato il disco VM |
| Immagine Docker | Riferimento immutabile letto dal lock; presenza nel motore non verificata |
| Git, Python 3.12, micro, Vagrant, VirtualBox | Attribuiti all'installer dai registri |
| WSL | Presente, non attribuito all'installer; selezionabile con consenso aggiuntivo. Distribuzione reale: `Ubuntu-24.04`, selezionabile separatamente |
| Docker Desktop | Non rilevato dal registro; CLI non disponibile. La pulizia dei suoi dati è stata verificata soltanto con simulazioni |
| Collegamenti | Voce selezionabile, nessuna pulizia eseguita |

Nessuna casella preselezionata. Confronto SHA-256 dei file del registro prima
e dopo l'anteprima estesa ai componenti esterni: invariati. Il rilevamento WSL
ha richiesto uscita dalla sandbox. La prova reale ha individuato due difetti
nel probe (valore accessorio della copia asincrona e switch quotati interpretati
da WSL come comando Linux): corretti e coperti da regressioni. Il precedente
resoconto senza distribuzioni era errato; l'elenco corretto contiene
`Ubuntu-24.04`. L'anteprima con sola selezione `wsl` si blocca finché questa
distribuzione viene conservata. L'anteprima con selezione esplicita
`wsl,wsl-distro:Ubuntu-24.04` è ammessa senza blocchi, ma non è stata eseguita.
Anche dopo questa prova i registri risultano invariati. Un tentativo fallito ha inoltrato `--list`
alla shell Linux; nessuna rimozione eseguita, stato precedente di esecuzione
della distribuzione non rilevato. Non è stato eseguito `wsl --shutdown`.
Anteprima con selezione `project`:
blocco atteso perché una VM verrebbe conservata. Nessun comando winget di
rimozione, Docker di rimozione, Vagrant destroy, elevazione o deploy eseguito.
Non aggiornati gli script già installati nel profilo utente.

Evidenza aggiornata: `tmp/selective-uninstall-external-preview.json`.
Scelta completa WSL ammessa: `tmp/selective-uninstall-wsl-selection-preview.json`.
Anteprima iniziale: `tmp/selective-uninstall-local-preview.json` e
`tmp/selective-uninstall-local-project-preview.json`. Procedure e contratti:
`installer/README.md`, sezione aggiornamento e disinstallazione Windows.

Verifiche: 102 test passati in quattro moduli (selezione, TUI, preflight,
errori scuola), parser PowerShell 3/3 e `git diff --check` superati. Il nuovo
modulo simula tutte le rimozioni e copre anche gli argomenti nativi del probe
con una fixture eseguibile, timeout/terminazione del figlio, isolamento da
contesti Docker remoti e verifica delle identità prima della pulizia.

## Prova successiva su macchina reale

1. Definire PC, componenti e risultato atteso; usare un checkout che contiene
   la modifica selettiva, oppure i launcher dopo una sua pubblicazione e aggiornamento.
2. Eseguire `-Preview` e verificare cartella, attribuzioni, componenti esterni,
   distribuzioni WSL e inventario Docker. Un'attribuzione storica non prova
   che il programma sia ancora installato. I dati Docker/WSL non sono inclusi
   nel backup del progetto e richiedono consenso distinto alla perdita definitiva.
3. Eseguire `-Preview -Components <id>` per la scelta concordata e leggere i blocchi.
4. Solo con autorizzazione esplicita della selezione concreta, aprire la lista
   interattiva. Verificare spazio per il backup prima di selezionare progetto/VM.
5. Dopo una rimozione autorizzata, controllare il componente scelto, l'integrità
   del backup, la conservazione delle voci escluse e la possibilità di riaprire
   il menu. Non chiudere le issue scuola sulla base della sola anteprima.

Per il pilot d'installazione scolastico rimangono da verificare diagnosi,
installazione e avvio Docker; raccogliere codici e log WSL/pairing se gli errori
persistono, senza credenziali, codici pairing o foto degli studenti. Non eseguiti
in questa fase installazioni reali, pairing remoto o prove di ripristino VM.

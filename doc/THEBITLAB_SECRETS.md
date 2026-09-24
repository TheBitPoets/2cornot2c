# Secret TheBitLab: configurazione AI, archivio e ripristino

Questa guida serve a chi configura o mantiene TheBitLab su un PC. Descrive la
ricerca di `ai.secret` usata dalla board e dal probe AI e il ruolo del repository
separato [thebitlab-secrets](https://github.com/kinderp/thebitlab-secrets).
Per l'uso dei provider nella board, vedere [COURSE_BOARD.md](COURSE_BOARD.md).

## Tre elementi distinti

| Elemento | Contenuto e funzione |
|---|---|
| Repository `2cornot2c` | Codice, test e documentazione di TheBitLab. Contiene i lettori delle configurazioni, non le credenziali reali |
| Repository privato `thebitlab-secrets` | Kit di conservazione e recupero: archivio cifrato `.7z`, inventario, script e istruzioni per gli operatori autorizzati |
| Cartella privata `~/.thebitlab-secrets` | File estratti e ripristinati sul PC, in chiaro e protetti dai permessi del filesystem; è la destinazione standard usata dai programmi |

Il repository `thebitlab-secrets` e la cartella `.thebitlab-secrets` **non sono
la stessa cosa**. Clonare il repository scarica il kit e l'archivio cifrato:
non installa le credenziali e non rende automaticamente disponibili le API key.
La board non consulta GitHub e non apre l'archivio durante la ricerca di `ai.secret`.

Su Windows, la cartella privata standard è:

```text
%USERPROFILE%\.thebitlab-secrets
```

Nel codice `~` indica la home dell'utente che esegue Python. Un altro account
Windows o un servizio avviato con un altro utente può quindi avere una home diversa.

## Perché esiste thebitlab-secrets

Il kit permette agli operatori autorizzati di conservare e recuperare su un
altro PC le credenziali necessarie senza inserirle nei commit del codice o
ricostruire manualmente i percorsi. Il README del kit documenta l'inventario e
gli script controllano il ripristino e gli accessi.

La separazione consente di gestire gli accessi al codice didattico e quelli
al materiale operativo in modo distinto. Il repository dei secret è destinato
agli operatori autorizzati; non è un prerequisito per gli studenti che usano
il corso o per chi configura il proprio ambiente con credenziali proprie.

Nell'archivio `.7z` sono cifrati sia i contenuti sia i nomi dei file. La password
va custodita separatamente dal repository. La visibilità privata di GitHub non
sostituisce la cifratura: i file estratti in chiaro non devono essere committati
nemmeno nel repository privato. I permessi della cartella runtime proteggono
l'uso locale; i suoi file non rimangono cifrati come nell'archivio.

Il kit non è un backup completo del servizio: dati applicativi, database,
configurazioni e procedure di recupero del server richiedono la propria gestione.

## Come vengono cercate le configurazioni AI

La logica condivisa è in [`scripts/ai_secret_store.py`](../scripts/ai_secret_store.py).
La usano [`course_board_server.py`](../scripts/course_board_server.py) e
[`probe_ai_payload_limit.py`](../scripts/probe_ai_payload_limit.py).
Non è una regola generale per tutte le credenziali di TheBitLab: SSH, GitHub App
e altri componenti mantengono le rispettive configurazioni.

Per ogni valore AI letto tramite `secret_value`, una variabile d'ambiente
**non vuota** con quel nome, per esempio `OPENAI_API_KEY`, ha precedenza.
Altrimenti il valore viene cercato in **un solo file**, scelto così:

| Ordine | File selezionato | Condizione |
|---|---|---|
| 1 | Percorso in `THEBITLAB_AI_SECRET_FILE` | La variabile è impostata a un valore non vuoto; il percorso deve essere assoluto |
| 2 | `~/.thebitlab-secrets/ai.secret` | Non c'è un percorso esplicito e questo percorso esiste |
| 3 | `<clone>/.secrets/ai.secret` | Non c'è un percorso esplicito e il file esterno standard è assente |

Il formato resta `NOME=valore`, una voce per riga; righe vuote e commenti che
iniziano con `#` vengono ignorati. Il file può contenere chiavi dei provider e
parametri AI letti dagli strumenti, come i nomi dei modelli. Non contiene JSON.

Non vengono uniti più file. Se il file selezionato non contiene una chiave,
questa non viene recuperata da un file a priorità inferiore. Un percorso
esplicito mancante non provoca un ripiego sul file standard o su quello del
clone; un percorso relativo esplicito viene rifiutato. Anche un file standard
presente ma vuoto non fa usare il file del clone. Un errore di lettura non
innesca un ripiego silenzioso.

Esempi di selezione, senza credenziali reali:

| Situazione | Risultato |
|---|---|
| Esistono sia il file esterno standard sia quello nel clone | Viene letto il file esterno |
| È configurato un percorso esplicito che non esiste | Nessun valore dal file; le singole variabili d'ambiente restano utilizzabili |
| È impostata `OPENAI_API_KEY`, mentre il file contiene anche altre chiavi | Per OpenAI prevale la variabile; gli altri valori possono provenire dal file selezionato |
| Due cloni sono eseguiti dallo stesso utente, senza override | Condividono il file esterno standard |

Per configurazioni separate tra cloni, indicare un file privato diverso nella
sessione da cui si avvia ciascuno strumento. Esempio PowerShell, con un percorso
personalizzato già predisposto e protetto:

```powershell
$env:THEBITLAB_AI_SECRET_FILE = "$env:USERPROFILE\TheBitLab-private\ai.secret"
python scripts/course_board_server.py
```

Equivalente in una shell Linux/macOS:

```bash
export THEBITLAB_AI_SECRET_FILE="$HOME/.thebitlab-private/ai.secret"
python scripts/course_board_server.py
```

Eseguire dalla radice del clone, con il suo ambiente Python attivo. Questi esempi
impostano il percorso nella sessione corrente: non creano il file e non modificano
configurazioni persistenti. In un servizio, impostare la variabile nell'ambiente
del processo interessato. Il lettore Python supporta questi percorsi; il kit di
ripristino descritto sotto è invece collaudato su Windows PowerShell 5.1 e NTFS.

## Cosa è cambiato rispetto al ripristino precedente

Prima, il ripristino collocava `ai.secret` in `<clone>/.secrets/ai.secret`.
Per farlo imponeva i controlli di sicurezza anche al clone e ai suoi antenati.
Un clone con permessi aggiuntivi per gli strumenti di sviluppo poteva essere
rifiutato con l'errore «Cartella antenata condivisa o non protetta».

Adesso tutti i 16 file vengono ripristinati nella cartella privata esterna,
incluso `ai.secret`. I controlli sui permessi e sugli antenati della destinazione
rimangono obbligatori. Il clone resta nella posizione scelta e lo script non
ne modifica i permessi. È stato inoltre corretto il modo in cui lo script
applica le ACL, senza richiedere privilegi di auditing all'utente ordinario.

La modifica in `2cornot2c` aggiunge la ricerca esterna condivisa da board e probe.
La copia storica `<clone>/.secrets/ai.secret` resta un'opzione di compatibilità:
non viene spostata o cancellata, ma non prevale su un file esterno selezionato.
Il vecchio percorso `<clone>/scripts/.secrets/ai.secret` non è letto.

Prima di usare il ripristino aggiornato, il clone deve includere
`scripts/ai_secret_store.py` e gli aggiornamenti ai due consumatori. Lo script
rifiuta un progetto privo del modulo per evitare un ripristino che il progetto
non saprebbe utilizzare. Per i nuovi ambienti usare la destinazione esterna;
non è necessario creare un'altra copia di `ai.secret` nel clone.

## Dal recupero alla verifica

La procedura dettagliata e l'inventario sono mantenuti nel
[README di thebitlab-secrets](https://github.com/kinderp/thebitlab-secrets/blob/main/README.md),
accessibile a chi ha i permessi sul repository. In sintesi:

1. Estrarre l'archivio con 7-Zip in una cartella privata fuori dai repository,
   inserendo localmente la password dell'archivio.
2. Eseguire `Restore-Secrets.ps1 -DryRun` per verificare sorgenti, destinazioni,
   permessi e conflitti; poi eseguire il ripristino senza `-DryRun`.
3. Lo script conserva i file già identici e si ferma davanti a file diversi,
   senza sovrascriverli. Nel `runtime.json` della GitHub App adatta i percorsi
   al PC di destinazione. Non crea token GitHub e conserva i file sorgenti.
4. Eseguire `Test-Secrets.ps1` per verificare il risultato e gli accessi.

Per esempio, con i due cloni sotto `dev` nel profilo Windows:

```powershell
powershell.exe -NoProfile -File "$env:USERPROFILE\dev\thebitlab-secrets\Test-Secrets.ps1" -ProjectPath "$env:USERPROFILE\dev\2cornot2c"
```

Il checker usa la `.venv` del clone: verifica file e permessi, dipendenze,
selezione AI, accessi AI e GitHub tramite richieste di sola lettura e accesso
SSH tramite il comando remoto `true`. La passphrase SSH, se richiesta, va
inserita nella console; è distinta dalla password dell'archivio. La console
attende Invio al termine per lasciare leggibile l'esito.

`-LocalOnly` limita i controlli al PC; `-NonInteractive` evita prompt e pausa;
`-SourceDirectory` aggiunge il confronto con gli originali estratti.
Gli esiti sono `OK`, `FAIL`, `WARN` e `SKIP`. I codici di uscita sono 0 per
controlli selezionati riusciti, 1 per errori e 2 per verifiche incomplete o
configurazioni disallineate. Un controllo omesso non è una prova riuscita.

Il checker non prova inferenza AI, quote o disponibilità di ogni modello,
login OAuth completo, backup o tutte le operazioni applicative. L'elenco dei
limiti e le azioni per ciascun errore sono nel README del kit.

Con `-SecretsRoot` personalizzato, configurare anche i consumatori: per i due
strumenti AI impostare `THEBITLAB_AI_SECRET_FILE` al percorso assoluto del file
ripristinato. Il ripristino non imposta questa variabile e non riconfigura
automaticamente gli altri servizi.

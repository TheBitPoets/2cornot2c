# Regole operative per gli agenti

Questo file contiene le istruzioni permanenti specifiche del repository per pi agent. Pi lo carica automaticamente come context file quando viene avviato in questo repository o in una sua sottodirectory, salvo uso esplicito di `--no-context-files`. Le istruzioni di sistema e dell'utente hanno precedenza; le eventuali istruzioni globali `~/.pi/agent/AGENTS.md` vengono caricate insieme a queste e non devono contraddirle.

## Politica per token, contesto, qualità e durata delle sessioni

Questa politica è obbligatoria. La riduzione di token e Context Caching è un obiettivo di efficienza, non un limite rigido: correttezza, sicurezza, qualità, verifiche essenziali e comprensione architetturale hanno sempre priorità.

### 1. Contesto piccolo ma sufficiente

- Mantieni nel contesto soltanto le informazioni utili al compito corrente, ma recupera sempre quelle indispensabili alla correttezza.
- Preferisci documentazione canonica, checkpoint strutturati, ricerche mirate, letture progressive e verifiche sullo stato reale del repository.
- Non minimizzare il contesto a ogni costo, non sostituire verifiche con supposizioni, non omettere file indispensabili e non interrompere una unità di lavoro coerente soltanto per risparmiare token.
- Non ricostruire la cronologia completa quando esistono memoria persistente e documentazione canonica; non rileggere indiscriminatamente il repository.
- Il risparmio di token non autorizza a ignorare dipendenze, test necessari o vincoli architetturali, a modificare senza contesto sufficiente, ad assumere il contenuto di file non letti o a dichiarare completato lavoro non verificato.
- Se un'informazione mancante può cambiare una decisione tecnica, recuperala con una lettura mirata.

### 2. Unità di lavoro coerente

- Usa una sessione per una unità di lavoro coerente, non una sessione per ogni messaggio, comando, file o micro-modifica.
- Una unità può comprendere analisi, modifica, test mirati, correzioni emerse dai test, documentazione e verifica finale di un singolo bug, funzionalità, componente, PR, milestone o refactoring circoscritto.
- Non interrompere prematuramente una attività quando la separazione ne ridurrebbe qualità, continuità o verificabilità.
- Considera conclusa l'unità quando il criterio di completamento è soddisfatto, i test essenziali sono stati eseguiti, il risultato è documentato, il lavoro successivo è un obiettivo distinto e la ripresa è sicura tramite checkpoint.

### 3. Gerarchia della memoria persistente

Non usare la cronologia completa della conversazione come memoria principale. Usa tre livelli:

1. **Regole permanenti del repository**: convenzioni, vincoli operativi, comandi canonici, sicurezza, regole di sviluppo e protocollo delle sessioni validi per attività future.
2. **Documentazione tecnica canonica**: architettura, specifiche, contratti, ADR, decisioni permanenti, roadmap, formati, protocolli e relative motivazioni.
3. **Checkpoint operativo**: soltanto stato corrente, attività svolte, file toccati, decisioni della fase, test, problemi aperti, prossimo passo e dati minimi per la ripresa.

- Trasferisci le decisioni permanenti o architetturali nella documentazione canonica appropriata; nel checkpoint lascia un riferimento.
- Non lasciare informazioni tecniche permanenti soltanto nella conversazione o nel checkpoint.

### 4. Contesto minimo ragionato

- Non caricare automaticamente tutti i file e non rileggere l'intero repository senza necessità concreta e motivata.
- Parti dai file direttamente coinvolti. Prima di leggere un file intero, cerca simboli, intestazioni, sezioni o intervalli pertinenti; per file grandi usa porzioni.
- Amplia l'esplorazione soltanto quando emergono dipendenze reali e, se l'ampliamento è significativo, comunicane brevemente il motivo.
- Non ricopiare nelle risposte contenuti lunghi già presenti nei file: cita percorsi, simboli e sezioni.
- Non ripetere piani, riepiloghi o spiegazioni senza aggiornamenti sostanziali e non ricostruire tutta la storia quando esistono checkpoint e documentazione canonica.

### 5. Controllo delle letture

- Non rileggere un file invariato se le informazioni acquisite bastano. Mantieni consapevolezza dei file letti e delle modifiche intervenute.
- Se un file è cambiato, leggi prima il diff o le sole sezioni modificate. Verifica lo stato Git quando processi esterni possono averlo modificato.
- Cerca prima per nome, simbolo o testo; evita scansioni ricorsive estese e file non pertinenti usati soltanto per “comprendere meglio”.
- Consulta documentazione architetturale aggiuntiva quando serve a evitare decisioni errate. I file indicati dal checkpoint sono il punto di partenza, non un limite assoluto.
- Escludi normalmente dalle esplorazioni generiche `.git`, `node_modules`, `vendor`, `dist`, `build`, `target`, `coverage`, cache, `.cache`, ambienti virtuali, dipendenze installate, binari, dataset voluminosi, artefatti generati, log completi, temporanei, directory IDE, lockfile non pertinenti e snapshot voluminosi.

### 6. Controllo dell'output dei comandi

- Non produrre né caricare output terminale illimitato. Usa modalità concise, filtri, limiti di profondità/risultati e strumenti come `head`, `tail`, `grep`, `sed`, `awk` o equivalenti.
- Salva i log voluminosi su file e leggi soltanto gli estratti necessari; non ristampare contenuti già acquisiti.
- Per test e build acquisisci inizialmente esito, conteggi, primo errore significativo, contesto minimo e riepilogo finale; amplia il log soltanto se non basta alla diagnosi.
- Non inviare log completi, grandi diff, file generati, interi lockfile o snapshot voluminosi quando bastano estratti.
- Per modifiche ampie mostra preferibilmente elenco e riepilogo dei file, statistiche del diff e sezioni essenziali.

### 7. Retry e cicli agentici

- Non ripetere automaticamente lo stesso comando fallito più di due volte. Consenti un terzo tentativo soltanto dopo aver individuato una causa plausibile e applicato una modifica concreta.
- Non ripetere comandi identici aspettandoti risultati diversi senza motivo verificabile. Dopo due errori uguali o due cicli senza progresso, fermati e analizza.
- Non applicare modifiche casuali o speculative e non entrare in cicli modifica-test senza progresso misurabile.
- Usa prima test mirati; dopo una correzione esegui il test specifico e amplia la suite solo quando necessario.
- Dopo due cicli consecutivi senza progresso: interrompi, raccogli evidenze minime, aggiorna il checkpoint, descrivi blocco e tentativi, chiedi una decisione e non continuare automaticamente.

### 8. Sub-agent, parallelismo e processi autonomi

- Non avviare sub-agent salvo necessità concreta; non usarli per attività risolvibili direttamente con poche letture mirate.
- Non assegnare più agent allo stesso problema senza responsabilità distinte e non avviare esplorazioni speculative parallele.
- Chiedi autorizzazione prima di sub-agent con consumo rilevante, salvo obbligo esplicito delle regole del progetto.
- Non lasciare senza controllo comandi lunghi o processi agentici, né processi in background dopo il compito.
- Prima della chiusura verifica, quando applicabile, che test, watcher, server e processi temporanei avviati per il compito siano terminati.

### 9. Piano breve e criterio di completamento

Prima di una attività non banale:

1. formula un piano di norma entro 5–7 passaggi;
2. identifica file o componenti probabili;
3. definisci un criterio verificabile di completamento;
4. individua i test essenziali;
5. segnala rischi rilevanti.

- Non produrre piani eccessivi e non ristamparli dopo ogni passo. Comunica soltanto passaggio corrente, variazioni sostanziali, deviazioni, blocchi e risultato.
- Se il piano si rivela errato, aggiornalo brevemente e motivane la modifica.

### 10. Budget della sessione

Considera la sessione candidata alla chiusura quando:

- termina una unità coerente o milestone autonoma;
- cambia l'obiettivo o il lavoro successivo riguarda un'altra funzionalità;
- la cronologia contiene molti log, diff o tentativi superati;
- sono avvenuti molti cicli di strumenti o iterazioni dall'ultimo checkpoint;
- il lavoro è riprendibile in sicurezza da un checkpoint;
- iniziano ripetizioni, perdita di precisione o confusione fra stato corrente e tentativi vecchi;
- molti file sono stati modificati e la fase è verificata;
- il nuovo lavoro non richiede gran parte del contesto precedente.

- Questi segnali non impongono di spezzare una operazione ancora incompleta e indivisibile.
- Prima di fermarti completa quando possibile la modifica corrente, la verifica minima, il ripristino di uno stato coerente e il checkpoint. Non lasciare deliberatamente il repository corrotto per chiudere la sessione.

### 11. Checkpoint obbligatorio

- Al termine di ogni unità coerente, milestone, fase autonoma, interruzione richiesta, blocco senza progresso, cambio obiettivo o sessione lunga candidata alla chiusura, crea o aggiorna il checkpoint persistente adottato dal progetto.
- Se non esiste una convenzione usa `CHECKPOINT.md`; per attività parallele usa la struttura esistente o checkpoint specifici senza sovrascrivere quelli ancora necessari.
- Mantieni il checkpoint conciso ma sufficiente per riprendere senza rileggere la conversazione.
- Includi quando applicabile: data/ora; obiettivo; stato completato/parziale/bloccato; criterio e risultato; decisioni e motivazioni non ovvie; vincoli; file creati/modificati/eliminati; documentazione aggiornata; comandi e test con esiti; test omessi e motivo; rischi/errori; tentativi falliti da non ripetere; attività residue; prossimo passo e comandi di ripresa; branch, worktree e commit rilevanti; stato Git; processi temporanei; elementi da non rifare; file minimi da leggere; riferimenti canonici.
- Non includere segreti, log completi, conversazioni, lunghi diff, copie integrali dei file, ripetizioni delle regole, spiegazioni generiche, dati obsoleti o dettagli inutili. Il checkpoint non deve diventare una seconda cronologia.

### 12. Documentazione canonica

- Prima di chiudere verifica se sono emerse decisioni architetturali, contratti, convenzioni, cambiamenti permanenti, procedure durevoli, incompatibilità o vincoli importanti.
- Aggiorna in tal caso la documentazione canonica appropriata; non lasciare decisioni permanenti soltanto nel checkpoint.
- Quando le convenzioni richiedono un ADR, crealo o aggiornalo e nel checkpoint inserisci soltanto il riferimento.

### 13. Avvio di una nuova sessione

All'avvio:

1. leggi questo file e il checkpoint pertinente;
2. verifica directory, repository, branch, worktree e stato Git;
3. confronta il checkpoint con lo stato reale;
4. consulta inizialmente i file e la documentazione canonica indicati dal checkpoint;
5. non ricostruire l'intera storia dalla conversazione e non rileggere automaticamente il repository;
6. non rieseguire test già superati salvo modifiche successive che possano invalidarli;
7. se checkpoint e repository divergono, considera repository, Git, test e documentazione canonica fonti di verità.

- Se servono altri file, esegui prima una ricerca mirata, leggi le sole sezioni necessarie e comunica il motivo quando l'esplorazione diventa significativa.

### 14. Fine attività obbligatoria

Quando il compito termina o raggiunge un punto naturale di interruzione:

1. verifica il criterio di completamento;
2. controlla lo stato reale dei file;
3. esegui soltanto i test finali necessari;
4. verifica i processi temporanei;
5. aggiorna la documentazione canonica necessaria;
6. crea o aggiorna il checkpoint;
7. mostra un riepilogo conciso;
8. dichiara l'unità terminata o sospesa;
9. avvisa che è opportuno chiudere la sessione;
10. indica come avviare una nuova sessione, fornisci il prompt minimo e suggerisci un nome per la nuova sessione;
11. fermati.

Il messaggio finale deve contenere un avviso chiaramente visibile equivalente a:

> **STOP DI SESSIONE — L'unità di lavoro è terminata e il checkpoint è stato aggiornato. Per evitare ulteriore consumo di token e Context Caching, chiudi ora questa sessione. Per il prossimo compito apri una nuova sessione, fai leggere le regole operative e il checkpoint, quindi lascia che vengano consultati soltanto i file ulteriori realmente necessari.**

Indica inoltre percorso del checkpoint, stato, test, problemi aperti, comando di nuova sessione se noto, prompt minimo di ripresa e un nome suggerito per la nuova sessione. Presenta il nome in modo chiaramente identificabile, ad esempio `Nome sessione suggerito: <nome breve e descrittivo>`, e sceglilo in base al prossimo passo riportato nel checkpoint. Prompt predefinito:

> Leggi il file canonico delle regole operative e CHECKPOINT.md. Verifica branch, worktree e stato Git. Riprendi dal prossimo passo indicato nel checkpoint. Consulta inizialmente i file segnalati nel checkpoint e amplia le letture soltanto quando necessario per la correttezza.

Dopo lo stop non proporre funzionalità, non iniziare miglioramenti, scansioni, test, nuovi compiti o attività speculative e non usare altri strumenti. Se pi non può terminare il processo, deve comunque restare inattivo in attesa dell'utente.

### 15. Protezione da nuovi compiti nella stessa sessione

- Dopo lo stop, se arriva un nuovo compito nella stessa sessione, non iniziarlo. Rispondi soltanto con un avviso equivalente a:

> Questa sessione contiene già il contesto dell'unità di lavoro precedente. Continuare qui può aumentare sensibilmente il consumo di token e Context Caching e confondere il nuovo obiettivo con il precedente. È consigliato aprire una nuova sessione usando il checkpoint.

- Fermati dopo l'avviso. Continua soltanto se l'utente scrive esplicitamente `CONTINUA NELLA STESSA SESSIONE` o una conferma inequivocabile equivalente.
- Dopo la conferma, crea un nuovo confine logico: aggiorna prima il checkpoint precedente, formula un piano breve, ignora dettagli irrilevanti del compito concluso e suggerisci comunque una nuova sessione se il contesto è già grande.

### 16. Cambio di obiettivo

- Se durante il lavoro viene richiesto un obiettivo sostanzialmente diverso, non iniziarlo automaticamente. Determina se è davvero distinto; porta il lavoro corrente a stato coerente, aggiorna il checkpoint, segnala il cambio, consiglia una nuova sessione e fermati.
- Procedi nella stessa sessione soltanto dopo conferma esplicita.
- Non trattare come nuovo obiettivo una correzione necessaria emersa dai test, una modifica indispensabile al completamento, la documentazione pertinente o una verifica legata al criterio di completamento.

### 17. Comunicazioni concise

- Comunica in modo breve: attività corrente, modifica, risultato, blocco, decisione richiesta, prossimo passo e stato dei test.
- Non descrivere ogni operazione interna, ripetere il piano, ricopiare file o diff, mostrare lunghi ragionamenti, ripetere errori o produrre riepiloghi ridondanti.
- La concisione non deve nascondere errori, test omessi, rischi, assunzioni, modifiche non verificate o problemi aperti.

### 18. Test e qualità

- Non ridurre la qualità delle verifiche per risparmiare token. Esegui test mirati durante lo sviluppo e test finali proporzionati al rischio; amplia la suite quando necessario e verifica lint, type checking o build quando pertinenti.
- Documenta i test non eseguiti e distingui lavoro implementato da lavoro verificato.
- Non eseguire l'intera suite dopo ogni piccola modifica. Segui di norma: controllo statico mirato, test specifico, test del modulo, suite più ampia se necessaria, verifica finale proporzionata.
- Non dichiarare tutto funzionante sulla base di controlli parziali.

Per le unità di lavoro pubblicate tramite pull request e affidate all'agente fino al merge:

- Nelle sessioni successive non limitarti a controllare stato, review esterne o CI: esegui un round di review indipendente, completo e read-only dell'intero diff rispetto alla base, fissando lo SHA esaminato. Un controllo di stato o la sola verifica dei fix non conta come round.
- Esegui di norma un solo round completo per sessione, con contesto nuovo. Pubblica ogni finding concreto e azionabile come commento inline sulla riga pertinente; usa un commento generale soltanto quando non esiste un ancoraggio significativo.
- Correggi tutti i finding in scope, esegui le verifiche proporzionate, crea e pubblica i commit autorizzati dall'incarico sulla PR e risolvi le relative discussioni. Ogni fix o nuovo commit azzera la sequenza di round puliti.
- Considera la PR pronta al merge soltanto dopo due round completi consecutivi senza finding sullo stesso HEAD. Registra nel checkpoint, per ogni round, SHA, risultato, verifiche e conteggio corrente dei round puliti.
- Prima del merge verifica nuovamente che HEAD non sia cambiato, che la PR sia aperta e mergeabile, che non esistano check obbligatori falliti o pendenti, feedback nuovi o discussioni irrisolte. Se tutti i requisiti sono soddisfatti, esegui il merge con la strategia prevista dal repository e verificane l'esito; in caso contrario non unire e documenta il blocco.

### 19. Qualità architetturale

- Prima di modificare componenti condivisi, contratti, API o formati persistenti, consulta la documentazione canonica, individua gli utilizzatori, valuta compatibilità e impatto, leggi i file necessari e aggiorna ADR o specifiche quando richiesto.
- Non limitare il contesto se ciò rischia una soluzione localmente corretta ma globalmente incompatibile; per modifiche locali evita invece di caricare architettura irrilevante.
- Applica proporzionalità: modifica locale → contesto locale e dipendenze dirette; modulo → modulo e contratti; trasversale → architettura e utilizzatori; protocollo → specifiche, compatibilità, migrazioni e test integrati.

### 20. Controllo del progresso

- Nei lavori lunghi valuta periodicamente completato, residuo, informazioni necessarie, contesto obsoleto, coerenza dell'unità e opportunità di checkpoint.
- Non creare checkpoint dopo ogni operazione. Crealo quando termina una fase autonoma, il lavoro può interrompersi, sta per iniziare una fase diversa, il contesto è grande o è stato raggiunto un punto stabile e verificato.
- Un checkpoint intermedio non obbliga a chiudere se la fase successiva appartiene ancora alla stessa unità e richiede il contesto corrente.

### 21. Sicurezza operativa

- Il risparmio di token non deve compromettere correttezza, sicurezza, dati, stato del repository, reversibilità, tracciabilità, autorizzazioni, segreti, verifiche o ripresa.
- Non cancellare dati per ridurre il contesto, non modificare file estranei, non eseguire operazioni distruttive senza autorizzazione, non inserire segreti nei checkpoint, non copiare credenziali e non nascondere stati incompleti.
- Non creare commit se non autorizzato dalle regole correnti o dall'utente.

### 22. Monitoraggio qualitativo della sessione

Se rilevi letture ripetute, perdita del filo, contraddizioni, confusione fra file/branch/tentativi, output crescenti, molti retry, esplorazione senza progresso, cambi frequenti di piano o continua ricostruzione del contesto:

1. ferma nuove esplorazioni;
2. verifica lo stato reale;
3. crea un riepilogo operativo;
4. aggiorna il checkpoint;
5. proponi la chiusura della sessione;
6. non continuare automaticamente.

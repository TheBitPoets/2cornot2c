# ADR: transizione dal bootstrap corrente al TheBitLab Standalone Agent

## Stato

Accettato.

## Contesto

TheBitLab utilizza attualmente un percorso di bootstrap e installazione locale che consente di preparare i PC degli studenti e del laboratorio installando o configurando i prerequisiti necessari all'esecuzione degli ambienti didattici. Questo percorso è già necessario per l'uso del sistema nell'anno scolastico 2026/2027 e non può essere abbandonato nel breve periodo; tuttavia, l'esperienza reale sui PC degli studenti ha evidenziato una fragilità significativa dovuta all'eterogeneità degli host Windows, allo stato delle sessioni e del `PATH`, ai package manager, ai privilegi amministrativi, ai riavvii, alla virtualizzazione e alle dipendenze di sistema come WSL, Docker, Vagrant e VirtualBox. Di conseguenza, il percorso corrente deve continuare a essere stabilizzato per sostenere il pilot in corso, ma non deve essere assunto come architettura definitiva per il provisioning degli ambienti TheBitLab.

## Decisione

TheBitLab adotterà una strategia di transizione a due binari. Il percorso di installazione corrente rimarrà supportato e verrà corretto nei difetti che ne compromettono l'uso reale, con priorità ai problemi che bloccano il deploy, il pilot e il lavoro degli studenti. In parallelo verrà progettato e sviluppato un nuovo **TheBitLab Standalone Agent**, distribuito come componente autonomo e destinato progressivamente a diventare il punto di ingresso standard di una macchina nel sistema TheBitLab. La sostituzione del percorso corrente non avverrà tramite una migrazione “big bang”: i due percorsi coesisteranno fino a quando il nuovo Agent non avrà dimostrato, attraverso test end-to-end su macchine reali, di poter sostenere almeno gli stessi casi d'uso necessari al pilot.

## Principi architetturali

Il nuovo TheBitLab Standalone Agent dovrà essere progettato come un componente minimo, autonomo e affidabile. Il suo funzionamento di base non dovrà dipendere dalla presenza preventiva di Python, Git o di altri strumenti dell'ambiente di sviluppo sul computer ospite. L'Agent dovrà essere in grado di identificare l'host, rilevarne le capacità, verificare lo stato dei provider disponibili e fornire a TheBitLab un profilo attendibile della macchina prima di tentare qualsiasi modifica o provisioning.

Le dipendenze dovranno essere distinte in categorie con responsabilità diverse: componenti incorporati nell'Agent, strumenti user-space che TheBitLab può gestire direttamente, provider di sistema come WSL o runtime container che richiedono integrazione con il sistema operativo, e prerequisiti esterni che TheBitLab può diagnosticare ma non deve modificare automaticamente, come impostazioni firmware, policy amministrative o restrizioni imposte dall'organizzazione.

Ogni provider gestito dal nuovo percorso dovrà esporre un modello operativo uniforme basato almeno sulle capacità di **probe**, **diagnose**, **repair** e **verify**; l'installazione automatica sarà disponibile solo per i provider per i quali può essere eseguita in modo sicuro e prevedibile. La semplice presenza di un eseguibile non sarà considerata sufficiente: una capability sarà dichiarata disponibile solo dopo una verifica funzionale del comportamento richiesto.

L'Agent non dovrà essere progettato esclusivamente per il singolo PC dello studente. Lo stesso componente dovrà poter costituire in futuro la base per la gestione centralizzata dei laboratori, per il deployment controllato da una postazione tecnica e per host avviati tramite ambienti TheBitLab Live o PXE. Questi scenari futuri non fanno parte dell'implementazione iniziale, ma il nuovo percorso non dovrà introdurre scelte che li rendano incompatibili o richiedano una seconda architettura parallela.

## Strategia di transizione

La migrazione verso il nuovo Agent sarà incrementale e dovrà preservare la continuità operativa dell'anno scolastico in corso. Il percorso di installazione esistente rimarrà il meccanismo operativo di riferimento finché il nuovo Agent non avrà superato gate espliciti di maturità. Durante questa fase, il lavoro sul percorso corrente sarà limitato a correzioni di stabilità, diagnostica, recovery e compatibilità necessarie al pilot; non dovrà essere esteso con nuove responsabilità architetturali che appartengono al nuovo Agent.

Il nuovo percorso verrà introdotto inizialmente in parallelo, prima come componente di diagnosi e inventario dell'host e successivamente come gestore di un numero ristretto di provider. La sua adozione verrà ampliata solo dopo verifiche su macchine reali, includendo almeno installazione pulita, aggiornamento, riavvio, ripresa dopo errore, utilizzo su rete scolastica e completamento di un flusso studente end-to-end.

Il percorso corrente potrà essere dichiarato **maintenance-only** solo quando il nuovo Agent sarà in grado di sostenere senza dipendenze manuali il percorso minimo necessario al pilot: installazione o avvio del core, autenticazione, rilevamento delle capability, preparazione dell'ambiente richiesto da almeno una Activity reale, esecuzione dell'attività e restituzione dei risultati al sistema TheBitLab. La successiva deprecazione dell'installer corrente richiederà evidenza di utilizzo stabile su un insieme rappresentativo di PC del laboratorio e dispositivi degli studenti.

## Conseguenze e trade-off

La strategia scelta comporta un periodo temporaneo in cui TheBitLab dovrà mantenere due percorsi di bootstrap e provisioning. Questo aumenta il costo di manutenzione nel breve periodo, ma riduce il rischio di interrompere il pilot durante una migrazione prematura e permette di confrontare il nuovo Agent con problemi reali già osservati sul percorso corrente.

La nuova architettura introduce un confine più netto tra il core TheBitLab e le dipendenze del sistema ospite. Questo dovrebbe ridurre la quantità di stato implicito e di assunzioni sull'host, ma richiederà la definizione di contratti stabili per capability, provider, diagnostica e verifica funzionale. Una parte della complessità che oggi è distribuita tra script di bootstrap dovrà quindi essere resa esplicita nel modello dell'Agent.

La scelta di non incorporare automaticamente ogni dipendenza di sistema implica che alcune configurazioni resteranno non riparabili senza intervento amministrativo. In questi casi TheBitLab dovrà privilegiare una diagnosi precisa e un comportamento fail-safe rispetto a tentativi aggressivi di modifica dell'host. L'affidabilità del sistema sarà quindi misurata non dalla capacità di installare qualunque stack su qualunque macchina, ma dalla capacità di determinare in modo affidabile cosa è supportato, cosa è riparabile e quando è necessario scegliere un percorso alternativo.

La futura gestione centralizzata dei laboratori, gli ambienti Live/PXE e gli executor remoti potranno riutilizzare il modello dell'Agent, ma non sono prerequisiti per la prima migrazione. La progettazione dovrà mantenerne aperta la possibilità senza rallentare il completamento del percorso minimo necessario al pilot corrente.

## Fuori scope e decisioni rinviate

Questo ADR non definisce la tecnologia con cui verrà realizzato o pacchettizzato lo Standalone Agent, né impone l'uso di PyInstaller, Nuitka, Go, Rust o altre soluzioni. La scelta dovrà essere effettuata con uno spike separato sulla base di portabilità, dimensione, aggiornabilità, firma del binario, tempi di startup, gestione delle dipendenze e manutenzione del codice esistente.

Non vengono inoltre definiti in questo ADR il protocollo di comunicazione tra Agent e control plane, il meccanismo di deployment centralizzato, l'eventuale uso di WinRM, SSH, Active Directory, Intune o altri strumenti di gestione remota, né il modello definitivo di autenticazione e autorizzazione per operazioni amministrative sugli host.

Restano fuori scope della prima implementazione dello Standalone Agent anche la costruzione di una distribuzione TheBitLab Live, il boot da USB, il network boot/PXE, il provisioning di immagini NixOS o equivalenti e l'esecuzione remota su worker o infrastrutture cloud. Questi scenari costituiscono evoluzioni previste e dovranno poter riutilizzare capability, profilo macchina e contratti dei provider definiti per l'Agent, ma richiederanno decisioni architetturali dedicate.

Questo ADR non stabilisce infine quali provider debbano essere supportati permanentemente. WSL, container runtime, Vagrant, VirtualBox, Hyper-V e altri strumenti verranno valutati in base ai casi d'uso reali e all'affidabilità osservata. In particolare, l'esistenza di un provider nel percorso di installazione corrente non implica che esso debba necessariamente essere migrato nel nuovo modello.

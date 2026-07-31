# Matrice di copertura TPSI quarto anno

Questa matrice controlla la fedeltà curricolare del pacchetto senza misurare la somiglianza testuale con il libro adottato.

Legenda stato:

- **baseline**: teoria, esempi, esercizi e proposta di laboratorio presenti nel modulo;
- **pilot activity**: almeno una activity assegnabile è già inclusa;
- **activity da creare**: il contenuto è presente, ma mancano package e test per la dashboard;
- **revisione docente**: è richiesta una verifica didattica o tecnica prima della pubblicazione;
- **licenza da verificare**: il frammento della fonte tecnica contiene materiale esterno da controllare o sostituire.

## Processi sequenziali e paralleli

| Voce curricolare | Contenuto originale | Collegamenti Linux | Attività/laboratorio | Stato |
| --- | --- | --- | --- | --- |
| Il modello a processi | `01_PROCESSI_E_CONCORRENZA.md` → Dal programma al processo; stati e ciclo di vita | `Linux Programming` → Processi; Process IDs; vedere i processi attivi | osservazione PID/PPID; albero dei processi; laboratorio `fork`/pipe | baseline, pilot activity |
| Risorse e condivisione | `01_PROCESSI_E_CONCORRENZA.md` → Spazio di indirizzamento e risorse | processi vs thread; dati specifici del thread | confronto memoria separata/condivisa; tabella delle risorse | baseline, activity da creare |
| I thread o processi leggeri | `01_PROCESSI_E_CONCORRENZA.md` → Thread e processo; confronto C/Java | I Thread; creazione, dati, join, ritorno, attributi | contatore concorrente; Java `Runnable`; debug di una race | baseline, activity da creare |
| L'elaborazione concorrente | `01_PROCESSI_E_CONCORRENZA.md` → Concorrenza, parallelismo e interleaving | thread sincroni e asincroni; processi vs thread | simulazione di interleaving; misurazione tempi | baseline, activity da creare |
| La descrizione della concorrenza | `01_PROCESSI_E_CONCORRENZA.md` → Tracce, invarianti e proprietà | sezioni critiche; race condition | diagramma degli eventi; proprietà safety/liveness | baseline, activity da creare |

## Comunicazione e sincronizzazione

| Voce curricolare | Contenuto originale | Collegamenti Linux | Attività/laboratorio | Stato |
| --- | --- | --- | --- | --- |
| La comunicazione tra processi | `02_COMUNICAZIONE_E_SINCRONIZZAZIONE.md` → IPC e canali | `fork`, `exec`, segnali, `wait`; estensione originale su pipe | pipe padre/figlio; protocollo a messaggi | baseline, pilot collegato |
| La sincronizzazione tra processi | `02_COMUNICAZIONE_E_SINCRONIZZAZIONE.md` → ordine, mutua esclusione e attesa | sincronizzazione e sezioni critiche; variabili di condizione | barriera concettuale; ordine di stampa deterministico | baseline, activity da creare |
| I semafori | `02_COMUNICAZIONE_E_SINCRONIZZAZIONE.md` → contatore e operazioni atomiche | Semafori | parcheggio con posti limitati; confronto `sem_t`/`Semaphore` | baseline, activity da creare |
| Applicazione dei semafori | `02_COMUNICAZIONE_E_SINCRONIZZAZIONE.md` → pattern di uso | Semafori; mutex e condition | turnazione, barriera, pool di risorse | baseline, activity da creare |
| Produttori/consumatori | `02_COMUNICAZIONE_E_SINCRONIZZAZIONE.md` → buffer limitato | mutex, semafori, variabili di condizione | coda circolare C; `BlockingQueue` Java | baseline, activity da creare |
| Lettori/scrittori | `02_COMUNICAZIONE_E_SINCRONIZZAZIONE.md` → politiche e starvation | deadlock con più thread; mutex | registro condiviso con politica esplicita | baseline, activity da creare |
| Deadlock | `02_COMUNICAZIONE_E_SINCRONIZZAZIONE.md` → condizioni e prevenzione | Mutex Deadlocks; Deadlocks con due o più Thread | laboratorio dei due lock; ordine globale | baseline, activity da creare |
| Monitor | `02_COMUNICAZIONE_E_SINCRONIZZAZIONE.md` → stato protetto e condition | mutex + variabili di condizione | monitor concettuale C; classe Java sincronizzata | baseline, activity da creare |
| Scambio di messaggi | `02_COMUNICAZIONE_E_SINCRONIZZAZIONE.md` → protocollo e ownership | segnali e processi; estensione originale IPC | mini servizio request/response | baseline, activity da creare |

## Requisiti software

| Voce curricolare | Contenuto originale | Fonte tecnica | Attività/laboratorio | Stato |
| --- | --- | --- | --- | --- |
| La specifica dei requisiti | `03_REQUISITI_SOFTWARE.md` → requisiti verificabili | documentazione interna del progetto e casi d'uso originali | riscrittura di requisiti vaghi; criteri di accettazione | baseline, activity da creare |
| Raccolta e analisi dei requisiti | `03_REQUISITI_SOFTWARE.md` → stakeholder, interviste e conflitti | issue e scenari del progetto come esempi | intervista simulata; matrice stakeholder/bisogni | baseline, activity da creare |
| Attori, casi d'uso e scenari | `03_REQUISITI_SOFTWARE.md` → use case e flussi | diagrammi Mermaid originali | modellazione dashboard docente/lab studente | baseline, activity da creare |
| Documentazione dei requisiti | `03_REQUISITI_SOFTWARE.md` → SRS leggera e tracciabilità | issue, decisioni e test di accettazione | mini specifica versionata | baseline, activity da creare |

## Documentazione del software

| Voce curricolare | Contenuto originale | Fonte tecnica | Attività/laboratorio | Stato |
| --- | --- | --- | --- | --- |
| La documentazione del progetto | `04_DOCUMENTAZIONE_VERSIONAMENTO.md` → pubblico, struttura e decisioni | documentazione esistente di 2cornot2c | creare README e ADR per un mini-progetto | baseline, activity da creare |
| La documentazione del codice | `04_DOCUMENTAZIONE_VERSIONAMENTO.md` → nomi, contratti, commenti e API | esempi originali C/Java | migliorare codice poco leggibile; generare documentazione | baseline, activity da creare |
| Controllo delle versioni | `04_DOCUMENTAZIONE_VERSIONAMENTO.md` → commit, branch, merge e review | Git e GitHub; workflow del repository | repository di squadra, conflitto guidato, pull request | baseline, activity da creare |

## Testing e debugging

| Voce curricolare | Contenuto originale | Fonte tecnica | Attività/laboratorio | Stato |
| --- | --- | --- | --- | --- |
| Verifica e validazione del software | `05_TESTING_DEBUGGING.md` → costruire bene/costruire il prodotto giusto | activity, rubriche e criteri di accettazione | derivare test dai requisiti | baseline, activity da creare |
| Verifica statica e dinamica | `05_TESTING_DEBUGGING.md` → review, warning, sanitizer, test | runner, GCC, test deterministici, sandbox | compilazione rigorosa; test; sanitizers | baseline, activity da creare |
| Debugging di un programma | `05_TESTING_DEBUGGING.md` → riproduzione, ipotesi, osservazione e fix | output runner e report | bug concorrente, deadlock e memoria | baseline, activity da creare |

## Cittadinanza digitale

| Nucleo | Contenuto originale | Attività | Stato |
| --- | --- | --- | --- |
| Licenze e uso corretto delle fonti | `06_CITTADINANZA_DIGITALE.md` | audit di provenienza e licenza | baseline, revisione docente |
| Collaborazione responsabile | `06_CITTADINANZA_DIGITALE.md` | code review rispettosa e segnalazione vulnerabilità | baseline, activity da creare |
| Privacy e dati scolastici | `06_CITTADINANZA_DIGITALE.md` | minimizzazione dati e ruoli | baseline, activity da creare |
| Sicurezza della supply chain | `06_CITTADINANZA_DIGITALE.md` | dipendenze, segreti e artefatti | baseline, activity da creare |
| Uso responsabile dell'AI | `06_CITTADINANZA_DIGITALE.md` | provenienza, verifica e policy di aiuto | baseline, activity da creare |

## Controllo della qualità didattica

Per ciascuna riga la revisione deve verificare:

1. corrispondenza tra obiettivi, teoria, esempio e attività;
2. presenza di almeno un errore frequente o caso limite;
3. progressione da osservazione a produzione autonoma;
4. distinzione fra concetto generale e dettaglio di una piattaforma;
5. presenza di una forma di verifica;
6. accessibilità del linguaggio e sintesi inclusiva;
7. riferimenti alle fonti e stato di licenza;
8. assenza di copie sostanziali del testo editoriale.

## Copertura `LINUX_PROGRAMMING.md`

Sezioni incluse nel lavoro di integrazione:

- Processi e Process IDs;
- visualizzazione e terminazione dei processi;
- `system`, `fork`, famiglia `exec`;
- segnali e `sigaction`;
- terminazione, `wait`, zombie e cleanup asincrono;
- thread POSIX, parametri, join, ritorno e attributi;
- cancellazione, dati specifici e cleanup handler;
- race condition e sezioni critiche;
- mutex, trylock e deadlock;
- semafori e variabili di condizione;
- implementazione Linux, `clone` e confronto processi/thread.

Sezione esclusa:

- `Controllo dei processi` e le relative slide iniziali.

Nota di licenza: gli esempi presenti nella dispensa che dichiarano una provenienza editoriale esterna devono essere controllati singolarmente. Dove la licenza non consente la redistribuzione o non è chiara, il pacchetto deve usare una nuova implementazione originale.

## Gap tecnici della piattaforma

| Gap | Impatto | Strategia iniziale |
| --- | --- | --- |
| runner Java non implementato | niente grading automatico Java | activity Java con rubrica docente e `test: false` |
| fonti remote non sincronizzate | repository privato non indicizzato automaticamente | fonte locale nel repository; migrazione futura al provider GitHub |
| content pack non ancora entità runtime | manifest non letto dalla dashboard | mantenere Markdown e activity come dati autorevoli correnti |
| collegamenti activity/UDA ancora in evoluzione | parte dei legami può essere manuale | ID stabili e `activity_ids` nel progetto archiviato |
| preview asset incompleta | immagini/diagrammi possono non rendersi | testo alternativo e diagrammi sorgente leggibili |

## Stato del primo incremento

Il primo incremento è completo quando sono presenti:

- contratto e manifest;
- tutti i moduli Markdown di baseline;
- progetto archiviato del quarto anno;
- una activity C/POSIX end-to-end con starter e soluzione docente;
- documentazione di importazione;
- PR draft collegata a #625.

La chiusura di #625 richiede invece tutte le activity principali, la revisione docente e il collaudo completo dalla dashboard.
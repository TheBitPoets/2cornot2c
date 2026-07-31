# Cittadinanza digitale per chi progetta software

<!--
content_id: tpsi4-content-cittadinanza-digitale
status: draft
curriculum_reference: tpsi4-curriculum-hoepli-volume-2
transformation: original-course-material
-->

## In questa unità impareremo

Al termine dell'unità lo studente dovrà saper:

- distinguere accesso a una risorsa e diritto di copiarla o redistribuirla;
- registrare autore, fonte, licenza, versione e trasformazioni;
- applicare minimizzazione, separazione dei ruoli e protezione dei dati scolastici;
- riconoscere segreti, dati personali e informazioni che non devono entrare nei repository;
- collaborare con issue, review e segnalazioni rispettose;
- usare strumenti AI dichiarando limiti, verifiche e responsabilità umana;
- ragionare su sicurezza della supply chain, dipendenze e artefatti;
- progettare contenuti accessibili e inclusivi;
- valutare l'impatto di automazione e metriche sugli studenti.

## Prerequisiti

Sono utili:

- fonti, repository e controllo di versione;
- ruoli docente/studente/amministratore;
- activity, test e report;
- concetti di autenticazione, autorizzazione e log;
- capacità di distinguere fatti, ipotesi e decisioni.

## Problema iniziale: posso copiare tutto se il repository è privato?

No. La privacy del repository controlla chi può accedere tramite la piattaforma, ma non modifica automaticamente copyright, licenze o condizioni d'uso della fonte.

Bisogna distinguere:

- **possesso o accesso**: posso leggere la risorsa;
- **uso personale**: posso usarla entro certi limiti;
- **riproduzione**: posso crearne copie;
- **modifica**: posso produrre opere derivate;
- **redistribuzione**: posso consegnarla ad altri;
- **pubblicazione**: posso renderla disponibile a un pubblico;
- **uso commerciale**: posso incorporarla in un prodotto o servizio a pagamento.

Le autorizzazioni possono essere diverse per ciascuna azione. In caso di dubbio si conserva soltanto il riferimento e si produce materiale originale.

Questa unità offre criteri didattici e tecnici; non sostituisce una consulenza legale o le condizioni specifiche della licenza.

## Copyright, licenza e pubblico dominio

Il copyright protegge automaticamente molte opere creative. Una licenza concede alcuni diritti secondo condizioni definite.

Domande da porre prima di importare una risorsa:

1. Chi è l'autore o titolare?
2. Qual è la licenza?
3. La licenza copre copia, modifica e redistribuzione?
4. Richiede attribuzione?
5. Impone di condividere con la stessa licenza?
6. Limita uso commerciale o opere derivate?
7. La risorsa contiene elementi con licenze diverse?
8. La piattaforma di accesso aggiunge condizioni contrattuali?
9. La versione è identificabile?
10. Possiamo rimuovere o aggiornare la risorsa se cambia lo stato?

L'assenza di una licenza esplicita non significa libertà di riuso.

## Provenienza

La provenienza descrive da dove deriva un'informazione e come è stata trasformata.

Campi utili:

```text
source_id
autore o organizzazione
titolo
provider
URI o repository
ref/versione
data di acquisizione
path/anchor/pagina
licenza
trasformazione
revisore
stato
```

### Quattro ruoli distinti

Nel pacchetto TPSI:

- il libro adottato è riferimento curricolare;
- `LINUX_PROGRAMMING.md` è fonte tecnica locale;
- i nuovi moduli sono elaborazione originale;
- il docente è revisore e responsabile della pubblicazione alla classe.

Dichiarare questa distinzione evita di attribuire al libro un testo che non contiene e di presentare un contenuto AI come fonte primaria.

## Citare non significa copiare integralmente

Una citazione breve e pertinente può servire a commentare o discutere. Una raccolta sistematica di estratti che ricostruisce l'opera può diventare una riproduzione sostanziale.

Strategia sicura per il corso:

- salvare il riferimento bibliografico;
- indicare capitolo o pagina per il docente;
- scrivere la spiegazione con parole e struttura proprie;
- creare esempi e tracce nuove;
- collegare eventuali risorse ufficiali senza incorporarle quando la licenza non è chiara;
- conservare nel manifest il tipo di relazione con la fonte.

## Dati personali nella scuola

Un dato personale può identificare direttamente o indirettamente una persona. In un contesto scolastico possono essere coinvolti:

- nome e account;
- email;
- classe;
- risultati;
- tentativi;
- errori;
- richieste di aiuto;
- tempi di lavoro;
- feedback;
- bisogni educativi;
- indirizzi IP o identificatori tecnici.

Non tutti i dati hanno lo stesso livello di sensibilità, ma devono essere raccolti con uno scopo definito.

## Minimizzazione dei dati

Principio pratico:

```text
raccogli soltanto ciò che serve
per il tempo necessario
con accesso limitato
```

Domande:

- Serve davvero il nome completo o basta un ID?
- Il prompt di aiuto deve contenere dati personali?
- Quanto tempo conserviamo i report?
- Chi può vedere i dettagli dei test?
- I log contengono file o token?
- I dati possono essere aggregati o pseudonimizzati?

Una funzionalità tecnicamente possibile non è automaticamente necessaria.

## Ruoli e autorizzazioni

Autenticazione e autorizzazione sono diverse:

- autenticazione: chi sei?
- autorizzazione: che cosa puoi fare?

Esempio di matrice:

| Operazione | Studente | Docente | Amministratore |
| --- | --- | --- | --- |
| leggere propria consegna | sì | sì | secondo ruolo |
| leggere soluzione docente | no | sì | secondo necessità |
| modificare activity | no | sì | secondo policy |
| vedere risultati di altri studenti | no | classe assegnata | secondo policy |
| configurare provider | no | limitato | sì |

La UI nascosta non è un controllo di autorizzazione. Il server deve applicare la regola.

## Segreti

Sono segreti:

- password;
- token API;
- chiavi private;
- cookie di sessione;
- codici temporanei;
- credenziali cloud;
- stringhe di connessione sensibili.

Non devono comparire in:

- repository;
- issue;
- screenshot;
- log;
- prompt inviati senza necessità;
- file di esempio realistici;
- report pubblici.

Se un segreto viene pubblicato, cancellarlo dall'ultimo commit non basta. Va revocato o ruotato e può essere necessario rimuoverlo dalla storia.

## Supply chain del software

Un progetto dipende da:

- librerie;
- immagini container;
- compilatori;
- action CI;
- plugin;
- repository;
- pacchetti di sistema;
- modelli e provider AI.

Rischi:

- dipendenza compromessa;
- versione non riproducibile;
- pacchetto con nome simile;
- script di installazione non verificato;
- action referenziata da un tag modificabile;
- artefatto diverso da quello testato;
- licenza incompatibile.

Contromisure:

- versioni e digest;
- fonti ufficiali;
- aggiornamenti intenzionali;
- revisione delle dipendenze;
- privilegi minimi;
- separazione fra build non fidata e pubblicazione;
- prova dell'artefatto che verrà distribuito;
- possibilità di rollback.

## Responsabilità nella code review

La review protegge utenti e progetto. Deve essere:

- specifica;
- basata su evidenze;
- rispettosa;
- proporzionata al rischio;
- tracciabile;
- aperta alla discussione.

Esempio:

```text
Il test nascosto viene copiato perché visibility non è controllata in questo
ramo. Questo può esporre la soluzione agli studenti. Propongo una regressione
sullo scaffold prima del merge.
```

La persona non coincide con il difetto. Correggere il codice non richiede umiliare l'autore.

## Segnalazione responsabile delle vulnerabilità

Quando si individua una vulnerabilità:

- non pubblicare dettagli sfruttabili senza necessità;
- raccogliere evidenze minime;
- contattare il canale previsto;
- non accedere a dati altrui per dimostrare il problema;
- descrivere impatto e condizioni;
- collaborare alla verifica della correzione;
- rispettare leggi e policy.

In un laboratorio scolastico, le prove devono usare dati e ambienti predisposti.

## Uso responsabile dell'AI

Un modello AI può aiutare a:

- proporre esercizi;
- spiegare un errore;
- generare una bozza;
- confrontare soluzioni;
- creare test da revisionare;
- adattare il linguaggio.

Non deve essere trattato come:

- fonte automatica di fatti;
- giudice infallibile;
- sostituto della revisione docente;
- autorizzazione a copiare contenuti protetti;
- luogo in cui inviare segreti o dati personali senza base e protezioni.

## Provenienza delle trasformazioni AI

Registrare almeno:

```text
provider/modello
versione o data
prompt o obiettivo sintetico
fonti fornite
output selezionato
revisioni umane
test eseguiti
stato di approvazione
```

Il docente deve poter distinguere:

- contenuto originale verificato;
- bozza AI non approvata;
- estratto da fonte;
- soluzione docente;
- feedback automatico.

## Policy di aiuto allo studente

Possibili modalità:

- senza aiuto;
- sola teoria/dispense;
- feedback tecnico su compilazione e test;
- suggerimento graduato;
- AI assisted entro budget e con registrazione;
- studio guidato.

La policy deve essere visibile prima dell'attività. Un aiuto autorizzato non deve diventare una penalizzazione nascosta.

## Valutazione e automazione

Un punteggio automatico misura ciò che il test osserva. Può non misurare:

- comprensione;
- qualità della progettazione;
- collaborazione;
- chiarezza;
- originalità;
- correttezza in scenari non coperti.

La rubrica integra i test. Il docente mantiene responsabilità e possibilità di revisione.

Attenzione alle metriche:

- tempo online non equivale a impegno;
- numero di tentativi non equivale a incompetenza;
- richieste di aiuto non equivalgono a scorrettezza;
- velocità non equivale a comprensione.

## Accessibilità e inclusione

Un contenuto accessibile dovrebbe:

- usare heading gerarchici;
- avere testo alternativo per immagini;
- non affidarsi soltanto al colore;
- usare linguaggio chiaro;
- offrire sintesi e mappe;
- rendere copiabili comandi e codice;
- dichiarare prerequisiti;
- evitare animazioni o tempi non necessari;
- funzionare da tastiera;
- mantenere contrasto e dimensioni leggibili.

L'adattamento non consiste nel ridurre sempre gli obiettivi. Può offrire modalità diverse per raggiungerli e dimostrarli.

## Affidabilità delle informazioni

Prima di usare una fonte tecnica:

1. identifica autore e organizzazione;
2. controlla data e versione;
3. preferisci documentazione ufficiale o fonte primaria;
4. confronta affermazioni importanti;
5. separa fatti, opinioni e inferenze;
6. verifica esempi nel contesto reale;
7. registra ciò che resta incerto.

Un articolo popolare può essere utile per orientarsi, ma una specifica o documentazione ufficiale è più adatta per un contratto preciso.

## Impatto ambientale e uso delle risorse

Anche il software usa energia, hardware, rete e storage.

Scelte da valutare:

- ricostruzioni CI inutili;
- immagini container enormi;
- dati conservati senza scopo;
- modelli AI sproporzionati al compito;
- dispositivi sostituiti prematuramente;
- ambienti di laboratorio sempre accesi;
- duplicazione di artefatti.

Ottimizzare non significa sacrificare sicurezza o accessibilità. Significa misurare e ridurre sprechi senza spostare il costo sugli utenti.

## Errori frequenti

### «È online, quindi è libero»

La disponibilità pubblica non equivale a licenza di copia.

### «È per la scuola, quindi posso redistribuire tutto»

Le eccezioni e licenze hanno limiti. Va verificato il caso concreto.

### «Tolgo il nome e il dato non è più personale»

Altri campi possono rendere la persona identificabile.

### «Il token è in un repository privato»

Resta un segreto condiviso, copiabile, loggabile e potenzialmente esposto.

### «La CI è verde, quindi è sicuro»

Sono passati soltanto i controlli configurati.

### «Lo ha detto l'AI»

Serve una fonte o una verifica indipendente.

### «Più dati migliorano sempre la didattica»

Dati inutili aumentano rischio e possono produrre interpretazioni scorrette.

### «Accessibilità significa materiale più facile»

Significa rimuovere barriere e offrire modalità adeguate, non necessariamente ridurre la competenza attesa.

## Esercizi graduati

### Livello A — riconosci

1. Classifica dieci elementi come dato personale, segreto, dato pubblico o informazione da verificare.
2. Individua licenza e autore di tre risorse open source.
3. Trova dati sensibili in un log simulato.
4. Distingui autenticazione e autorizzazione.

### Livello B — correggi

1. Riscrivi un esempio che contiene una chiave API reale.
2. Aggiungi provenienza a una lezione senza fonti.
3. Migliora una activity che non dichiara la policy di aiuto.
4. Rendi accessibile una pagina che usa soltanto colori e immagini senza testo alternativo.

### Livello C — progetta

1. Costruisci una matrice ruoli/permessi per dashboard docente e studente.
2. Definisci una retention policy per report e richieste di aiuto.
3. Crea un manifest di fonti con licenza, versione e stato.
4. Progetta un flusso di segnalazione responsabile per una vulnerabilità.

### Livello D — analizza

1. Valuta rischi di una dipendenza non fissata a versione.
2. Analizza un prompt che contiene dati scolastici e proponi minimizzazione.
3. Individua bias possibili in una metrica di valutazione automatica.
4. Verifica se una copia di materiali editoriali può essere sostituita da contenuto originale e locator.

### Livello E — mini-progetto

Esegui un audit di un piccolo repository:

- fonti e licenze;
- segreti;
- dati personali;
- dipendenze;
- permessi;
- accessibilità;
- policy AI;
- retention;
- rischi e azioni prioritarie.

### Livello F — progetto integrato

Progetta la governance di un knowledge hub didattico federato:

- ruoli;
- provider;
- provenienza;
- versioni;
- licenze;
- revisione;
- rimozione;
- privacy;
- audit;
- uso AI;
- pubblicazione e rollback.

## Laboratorio 1 — audit di provenienza

Scegli una lezione e costruisci una tabella:

| Blocco | Fonte | Tipo di relazione | Licenza | Trasformazione | Stato |
| --- | --- | --- | --- | --- | --- |
| definizione | documentazione ufficiale | sintesi | verificata | parafrasi | reviewed |
| esempio | originale | nuova creazione | progetto | nessuna | draft |
| immagine | sito esterno | collegamento | da verificare | nessuna | blocked |

Sostituisci o blocca ogni elemento privo di base chiara.

## Laboratorio 2 — repository senza segreti

In un repository di prova:

1. configura file `.env.example` senza valori reali;
2. ignora `.env`;
3. usa secret del sistema CI;
4. simula un segreto pubblicato;
5. descrivi revoca, rotazione e pulizia della storia;
6. aggiungi un controllo automatico.

Non usare credenziali reali.

## Laboratorio 3 — policy AI per una verifica

Definisci:

- aiuti ammessi;
- aiuti vietati;
- dati che non devono essere inviati;
- budget;
- tracciamento;
- feedback visibile;
- responsabilità docente;
- procedura in caso di errore del provider.

Applica la policy a una activity e verifica che studente e docente vedano informazioni coerenti.

## Laboratorio 4 — accessibilità del contenuto

Valuta un modulo Markdown con una checklist:

- heading;
- link descrittivi;
- alternative testuali;
- tabelle leggibili;
- codice copiabile;
- sintesi;
- prerequisiti;
- contrasto nella preview;
- navigazione da tastiera;
- linguaggio.

Proponi modifiche senza alterare gli obiettivi disciplinari.

## Verifica rapida

1. Perché un repository privato non risolve automaticamente il copyright?
2. Quali informazioni descrivono la provenienza?
3. Qual è la differenza tra autenticazione e autorizzazione?
4. Che cosa significa minimizzazione dei dati?
5. Perché un token non deve entrare nei log?
6. Che cos'è la supply chain del software?
7. Come si formula una review rispettosa e utile?
8. Perché l'AI non è una fonte primaria?
9. Quali limiti ha una valutazione automatica?
10. Quali caratteristiche rendono accessibile un contenuto?

## Sintesi inclusiva

- Avere accesso a una risorsa non significa poterla copiare o distribuire.
- La licenza stabilisce gli usi concessi.
- La provenienza collega contenuto, autore, versione, licenza e trasformazioni.
- Raccogliere meno dati riduce rischi.
- Autenticare significa riconoscere l'utente; autorizzare significa controllare le operazioni.
- Password e token non devono comparire in repository o log.
- Dipendenze e action fanno parte della sicurezza del progetto.
- La review riguarda il cambiamento, non il valore della persona.
- L'AI produce bozze da verificare e non sostituisce fonti e responsabilità.
- Test e metriche non descrivono tutta la competenza di uno studente.
- Accessibilità significa rimuovere barriere mantenendo obiettivi chiari.

## Progetto finale suggerito

Integra i moduli del percorso in un progetto di gruppo:

```text
sistema concorrente o servizio locale
+ requisiti e casi d'uso
+ documentazione e Git
+ test e debugging
+ manifest di fonti
+ privacy, licenze e policy AI
+ demo e relazione finale
```

Il progetto viene valutato su correttezza, processo, evidenze, chiarezza, responsabilità e capacità di motivare le scelte.

## Fonti e note di revisione

- Riferimento curricolare: schede di cittadinanza digitale previste dall'indice pubblico del volume 2.
- Norme e licenze concrete devono essere verificate su fonti ufficiali aggiornate prima di una decisione operativa.
- Scenari, esercizi e testi sono originali.
- Stato: `draft`; revisione docente e, per aspetti legali o privacy reali, verifica con i referenti competenti.
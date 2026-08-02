# Cornice didattica di TheBitLab

## Scopo

TheBitLab sostiene un percorso di informatica in cui teoria, laboratorio, esercitazione, verifica e feedback condividono la stessa struttura. La piattaforma non sostituisce la progettazione del docente: rende espliciti obiettivi, fonti, vincoli di aiuto, prove e risultati, così lo studente può lavorare con maggiore autonomia senza perdere tracciabilità.

Il pilot 2026/2027 è pensato per una singola scuola e circa 120 studenti. L'MVP privilegia flussi verificabili e reversibili rispetto all'automazione completa.

## Principi didattici

1. **Il percorso viene prima dello strumento.** UDA, prerequisiti e calendario danno significato alle activity.
2. **Teoria e pratica restano collegate.** Ogni argomento può provenire da dispense locali o repository GitHub/GitLab fissati a commit.
3. **L'aiuto è una scelta didattica.** Il docente dichiara quali modalità sono ammesse per ogni activity.
4. **Il feedback deterministico precede l'AI.** Test, compilazione e rubriche producono evidenze ripetibili; l'AI può spiegare o proporre una bozza, non sostituire l'evidenza.
5. **La valutazione resta responsabilità del docente.** Bozze AI, tentativi e risultati tecnici sono separati dal voto approvato.
6. **Identità e autorizzazione sono interne.** Google e GitHub autenticando un utente non decidono ruolo, classe o permessi TheBitLab.
7. **La provenienza è parte del contenuto.** Fonte, commit e digest impediscono che un paragrafo cambi silenziosamente mentre viene usato in un percorso.

## Unità della progettazione

### Percorso e anno

Il percorso organizza uno o più anni di corso. Ogni anno contiene UDA ordinate e può essere associato a un calendario scolastico.

### UDA

Una UDA raccoglie:

- titolo, descrizione e durata;
- paragrafi teorici e laboratoriali;
- activity collegate come pratica o verifica;
- date pianificate e scadenze;
- stato di avanzamento effettivo;
- cornici didattiche generate o curate dal docente.

### Fonti

Le fonti Markdown possono essere:

- locali al repository TheBitLab;
- repository GitHub pubblici o privati;
- repository GitLab pubblici o privati.

Le fonti remote vengono lette tramite API e fissate a un commit immutabile. Le credenziali non fanno parte del progetto didattico. La Course Board conserva per ogni paragrafo identificativo della fonte, commit e digest del contenuto.

### Activity

Una activity descrive il lavoro richiesto, i file, la modalità di supporto, i test e la policy di grading. Nel percorso viene collegata senza duplicarne il contenuto autorevole.

Ruoli principali del collegamento:

- `practice`: esercitazione o laboratorio;
- `verification`: prova, verifica o attività valutativa.

### Calendario

Le date del percorso generano eventi derivati. Il calendario conserva gli eventi propri della scuola e non duplica gli eventi già derivabili dalle activity. Revisioni separate evitano che l'aggiornamento dell'avanzamento sovrascriva la progettazione.

## Modalità di aiuto

L'MVP distingue:

- **senza aiuto**: prova individuale o vincolo esplicito;
- **teoria/dispense**: richiamo a contenuti approvati;
- **errori e debug**: spiegazione tecnica basata sull'esecuzione;
- **AI assisted**: supporto generativo entro policy e budget;
- **feedback docente**: revisione umana e approvazione finale.

Le richieste di aiuto vengono registrate separatamente dai tentativi e non modificano automaticamente il voto.

## Ciclo docente

1. Definire o importare fonti.
2. Costruire UDA e calendario.
3. Creare e validare activity.
4. Collegare activity al percorso.
5. Assegnare activity a classi o studenti.
6. Monitorare tentativi, consegne e richieste di aiuto.
7. Leggere grading deterministico e bozze AI.
8. Approvare feedback e decisioni valutative.
9. Usare quadro classe e registro per riprogettare il percorso.

## Ciclo studente

1. Autenticarsi e appartenere a una classe autorizzata.
2. Consultare consegne e modalità di aiuto.
3. Lavorare nel repository o ambiente locale.
4. Eseguire il runner e leggere i singoli test.
5. Richiedere aiuto quando consentito.
6. Selezionare il tentativo definitivo secondo policy.
7. Consultare grading e solo feedback approvato.

## Ruolo dell'AI

L'AI può:

- proporre cornici didattiche;
- sintetizzare contesto verificato;
- assistere debug e studio;
- preparare bozze di feedback.

L'AI non può:

- leggere contenuti con provenienza obsoleta;
- approvare autonomamente un voto;
- aggirare budget o modalità di aiuto;
- ricevere credenziali, sessioni o token provider;
- sostituire il grading deterministico.

## Evidenze e trasparenza

Le evidenze principali sono:

- snapshot delle fonti;
- activity validate;
- tentativi e consegna definitiva;
- report dei test;
- richieste e risposte di aiuto;
- bozze e approvazioni del feedback;
- collegamenti a UDA e calendario.

La piattaforma separa dati autorevoli, viste derivate e cache. Un errore nella GUI non deve trasformarsi in perdita silenziosa o modifica concorrente.

## Inclusione e gradualità

Il docente può partire con CLI/TUI e dati demo, introdurre gradualmente dashboard e autenticazione federata e mantenere alternative non-AI. Le modalità di aiuto rendono visibili le differenze tra esercitazione guidata, laboratorio autonomo e verifica.

## Limiti pedagogici dell'MVP

- nessun modello sostituisce osservazione e colloquio docente;
- le metriche tecniche non misurano da sole comprensione o collaborazione;
- un test superato non equivale automaticamente al raggiungimento di una competenza;
- il pilot è mono-scuola e richiede procedure organizzative locali;
- accessibilità, privacy e conservazione dei dati vanno riesaminate con dati reali e policy scolastiche.

## Documenti collegati

- [Guida MVP 2026/2027](MVP_2026_2027.md)
- [Architettura MVP](ARCHITETTURA_MVP.md)
- [Course Board](COURSE_BOARD.md)
- [Activity e grading](ASSIGNMENTS.md)
- [Lab studente](STUDENT_LAB.md)
- [Modello dati](DATA_MODEL_MVP.md)

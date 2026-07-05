# Percorso didattico

Questo documento e generato automaticamente da `doc/course_design.json`.

Per modificarlo, aggiorna la struttura con la Course Design Board e poi rigenera il file.

## Sorgenti

- `README.md`
- `LINUX_PROGRAMMING.md`

## Sintesi dei percorsi

<table align="center">
<thead>
<tr>
<th align="center">Anno</th>
<th align="center">Descrizione</th>
<th align="center">Ore/settimana</th>
<th align="center">Settimane</th>
<th align="center">UDA</th>
<th align="center">Argomenti assegnati</th>
</tr>
</thead>
<tbody>
<tr>
<td align="center"><div align="justify">Terzo anno</div></td>
<td align="center"><div align="justify">Corso di C base e intermedio focalizzato sulla logica di programmazione e la gestione della memoria, con integrazione di attività di laboratorio.</div></td>
<td align="center"><div align="justify">3</div></td>
<td align="center"><div align="justify">33</div></td>
<td align="center"><div align="justify">9</div></td>
<td align="center"><div align="justify">136</div></td>
</tr>
<tr>
<td align="center"><div align="justify">Quarto anno</div></td>
<td align="center"><div align="justify">Linux programming, processi e thread</div></td>
<td align="center"><div align="justify">3</div></td>
<td align="center"><div align="justify">33</div></td>
<td align="center"><div align="justify">7</div></td>
<td align="center"><div align="justify">0</div></td>
</tr>
</tbody>
</table>

## Terzo anno

Corso di C base e intermedio focalizzato sulla logica di programmazione e la gestione della memoria, con integrazione di attività di laboratorio.

- Ore settimanali: `3`
- Settimane: `33`

<table align="center">
<thead>
<tr>
<th align="center">UDA</th>
<th align="center">Percorso</th>
<th align="center">Settimane</th>
<th align="center">Argomenti</th>
</tr>
</thead>
<tbody>
<tr>
<td align="center"><div align="justify"><code>uda-1</code> Strumenti, primo programma e rappresentazione</div></td>
<td align="center"><div align="justify">Base</div></td>
<td align="center"><div align="justify">3</div></td>
<td align="center"><div align="justify">25</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-2</code> Operatori, condizioni e selezione</div></td>
<td align="center"><div align="justify">Base</div></td>
<td align="center"><div align="justify">3</div></td>
<td align="center"><div align="justify">20</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-3</code> Cicli e funzioni</div></td>
<td align="center"><div align="justify">Base</div></td>
<td align="center"><div align="justify">4</div></td>
<td align="center"><div align="justify">6</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-4</code> Array e stringhe semplici</div></td>
<td align="center"><div align="justify">Base</div></td>
<td align="center"><div align="justify">4</div></td>
<td align="center"><div align="justify">7</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-5</code> Struct e consolidamento</div></td>
<td align="center"><div align="justify">Base</div></td>
<td align="center"><div align="justify">3</div></td>
<td align="center"><div align="justify">3</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-6</code> Puntatori, array e indirizzi</div></td>
<td align="center"><div align="justify">Intermedio</div></td>
<td align="center"><div align="justify">4</div></td>
<td align="center"><div align="justify">30</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-7</code> Memoria automatica, statica e dinamica</div></td>
<td align="center"><div align="justify">Intermedio</div></td>
<td align="center"><div align="justify">4</div></td>
<td align="center"><div align="justify">13</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-8</code> Preprocessore, header e compilazione separata</div></td>
<td align="center"><div align="justify">Intermedio</div></td>
<td align="center"><div align="justify">3</div></td>
<td align="center"><div align="justify">18</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-9</code> File, Makefile, debugging e progetto</div></td>
<td align="center"><div align="justify">Intermedio</div></td>
<td align="center"><div align="justify">5</div></td>
<td align="center"><div align="justify">14</div></td>
</tr>
</tbody>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-1 - Strumenti, primo programma e rappresentazione

<details>
<summary><strong>Apri contenuto UDA - Base - 3 settimane</strong></summary>

- Percorso: `Base`
- Settimane: `3`

#### Argomenti

- <details>
  <summary><a href="../README.md#introduzione">Introduzione</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sulla configurazione dell'ambiente, sugli strumenti di lavoro e sull'avvio del laboratorio. I sottoparagrafi collegati sono: Guest Additions. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Introduzione", lo studente dovrebbe aver seguito il lavoro precedente su "l'avvio del percorso e la costruzione delle basi operative":
      - saper compilare ed eseguire piccoli programmi C
      - leggere esempi guidati e riconoscere il lessico tecnico già introdotto.
      Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Introduzione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "l'avvio del percorso e la costruzione delle basi operative" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come una prosecuzione naturale, non come un blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Guest Additions". Durante la spiegazione, conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Introduzione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è quello di collegare questo argomento a "Guest Additions" oppure, se l'argomento ha sottoparagrafi, di affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md, sezione "Introduzione" (../README.md#introduzione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#guest-additions">Guest Additions</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per il Terzo anno. Serve a lavorare sul concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore "Introduzione". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Guest Additions", lo studente dovrebbe aver seguito il lavoro precedente su "Introduzione", sapere come compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve sapere spiegare il ruolo di "Guest Additions", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Introduzione" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Laboratori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Guest Additions", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Laboratori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md, sezione "Guest Additions" (../README.md#guest-additions). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#laboratori">Laboratori</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su organizzazione dei sorgenti, cartelle di lavoro e compilazione degli esercizi. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Laboratori" lo studente dovrebbe aver seguito il lavoro precedente su "Guest Additions", sapere come compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione, lo studente deve saper spiegare il ruolo dei "Laboratori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Guest Additions" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Il processo di compilazione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Laboratori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Il processo di compilazione" oppure, se l'argomento ha dei sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md, sezione "Laboratori" (../README.md#laboratori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#il-processo-di-compilazione">Il processo di compilazione</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sulla trasformazione del sorgente C in eseguibile tramite preprocessore, compilatore, assembler e linker. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Il processo di compilazione", lo studente dovrebbe aver seguito il lavoro precedente su "Laboratori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione, lo studente deve sapere spiegare il ruolo del "processo di compilazione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Laboratori" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Il primo programma in C". Durante la spiegazione, conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Il processo di compilazione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Il primo programma in C" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md, sezione "Il processo di compilazione" (../README.md#il-processo-di-compilazione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#il-primo-programma-in-c">Il primo programma in C</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su struttura minima di un programma C, funzione main, include e stampa a video. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Il primo programma in C", lo studente dovrebbe aver seguito il lavoro precedente su "Il processo di compilazione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione, lo studente deve sapere spiegare il ruolo di "Il primo programma in C", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Il processo di compilazione" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Variabili". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Il primo programma in C", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Variabili" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md, sezione "Il primo programma in C" (../README.md#il-primo-programma-in-c). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#variabili">Variabili</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Variabili", lo studente dovrebbe aver seguito il lavoro precedente su "Il primo programma in C", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve sapere spiegare il ruolo di "Variabili", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Il primo programma in C" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Rappresentazione delle informazioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Variabili", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è quello di collegare questo argomento a "Rappresentazione delle informazioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md, sezione "Variabili" (../README.md#variabili). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#rappresentazione-delle-informazioni">Rappresentazione delle informazioni</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su bit, byte, basi numeriche e interpretazione dei dati in memoria. I sottoparagrafi collegati sono: Big & Little endian, Codifica numeri decimali, Mapping signed - unsigned, Estensione della rappresentazione binaria di un numero intero, Troncamento della rappresentazione binaria di un numero, Addizione senza segno, Addizione con segno, Tipi di dato, `int`. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Rappresentazione delle informazioni", lo studente dovrebbe aver seguito il lavoro precedente su "Variabili", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Rappresentazione delle informazioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Variabili" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Big & Little endian". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Rappresentazione delle informazioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Big & Little endian" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md, sezione "Rappresentazione delle informazioni" (../README.md#rappresentazione-delle-informazioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#big-little-endian">Big &amp; Little endian</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sull'ordine dei byte in memoria e sulla lettura corretta dei valori multibyte. Si collega al blocco superiore "Rappresentazione delle informazioni". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Big & Little endian", lo studente dovrebbe aver seguito il lavoro precedente su "Rappresentazione delle informazioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Big & Little endian", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Rappresentazione delle informazioni" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Codifica di numeri decimali". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Big & Little Endian", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Codifica dei numeri decimali" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md, sezione "Big & Little endian" (../README.md#big-little-endian). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#codifica-numeri-decimali">Codifica numeri decimali</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sulla rappresentazione binaria dei numeri e sul significato dei bit. Si collega al blocco superiore "Rappresentazione delle informazioni". I sottoparagrafi collegati sono: Codifica interi senza segno, Codifica interi con segno (complemento a due). La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Codifica numeri decimali" lo studente dovrebbe aver seguito il lavoro precedente su "Big & Little Endian", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve sapere spiegare il ruolo di "Codifica di numeri decimali", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Big & Little endian" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Codifica interi senza segno". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Codifica numeri decimali", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Codifica interi senza segno" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md, sezione "Codifica numeri decimali" (../README.md#codifica-numeri-decimali). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    - <details>
      <summary><a href="../README.md#codifica-interi-senza-segno">Codifica interi senza segno</a> <code>README.md</code> H4 <code>draft</code></summary>

      - <details>
        <summary><strong>Cornice didattica</strong></summary>

        - <details>
          <summary><strong>Contesto</strong></summary>

          Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sulla rappresentazione binaria dei numeri e sul significato dei bit. Si collega al blocco superiore Rappresentazione delle informazioni > Codifica numeri decimali. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
          </details>
        - <details>
          <summary><strong>Prerequisiti</strong></summary>

          Prima di affrontare "Codifica interi senza segno", lo studente dovrebbe aver seguito il lavoro precedente su "Codifica numeri decimali", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
          </details>
        - <details>
          <summary><strong>Obiettivi</strong></summary>

          Alla fine della lezione, lo studente deve sapere spiegare il ruolo di "Codifica interi senza segno", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
          </details>
        - <details>
          <summary><strong>Richiamo</strong></summary>

          Richiama il passaggio precedente su "Codifica numeri decimali" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
          </details>
        - <details>
          <summary><strong>Anticipazione</strong></summary>

          Questo argomento prepara il lavoro successivo su "Codifica interi con segno (complemento a due)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
          </details>
        - <details>
          <summary><strong>Prossimo passo</strong></summary>

          Dopo la spiegazione, proponi un esempio minimo su "Codifica interi senza segno", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Codifica interi con segno (complemento a due)", oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
          </details>
        - <details>
          <summary><strong>Rimando</strong></summary>

          Riferimento principale: README.md, sezione "Codifica interi senza segno" (../README.md#codifica-interi-senza-segno). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
          </details>
        </details>
      </details>
    - <details>
      <summary><a href="../README.md#codifica-interi-con-segno-complemento-a-due">Codifica interi con segno (complemento a due)</a> <code>README.md</code> H4 <code>draft</code></summary>

      - <details>
        <summary><strong>Cornice didattica</strong></summary>

        - <details>
          <summary><strong>Contesto</strong></summary>

          Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sulla rappresentazione binaria dei numeri e sul significato dei bit. Si collega al blocco superiore Rappresentazione delle informazioni > Codifica dei numeri decimali. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
          </details>
        - <details>
          <summary><strong>Prerequisiti</strong></summary>

          Prima di affrontare "Codifica interi con segno (complemento a due)" lo studente dovrebbe aver seguito il lavoro precedente su "Codifica interi senza segno", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
          </details>
        - <details>
          <summary><strong>Obiettivi</strong></summary>

          Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Codifica interi con segno (complemento a due)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
          </details>
        - <details>
          <summary><strong>Richiamo</strong></summary>

          Richiama il passaggio precedente su "Codifica interi senza segno" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
          </details>
        - <details>
          <summary><strong>Anticipazione</strong></summary>

          Questo argomento prepara il lavoro successivo su "Mapping signed - unsigned". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
          </details>
        - <details>
          <summary><strong>Prossimo passo</strong></summary>

          Dopo la spiegazione, proponi un esempio minimo su "Codifica interi con segno (complemento a due)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Mapping signed - unsigned" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
          </details>
        - <details>
          <summary><strong>Rimando</strong></summary>

          Riferimento principale: README.md, sezione "Codifica interi con segno (complemento a due)" (../README.md#codifica-interi-con-segno-complemento-a-due). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
          </details>
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#mapping-signed---unsigned">Mapping signed - unsigned</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per terzo anno. Serve a lavorare su numeri con segno, complemento a due, range e casi limite. Si collega al blocco superiore "Rappresentazione delle informazioni". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Mapping signed - unsigned" lo studente dovrebbe aver seguito il lavoro precedente su "Codifica interi con segno (complemento a due)", saper compilare ed eseguire piccoli programmi in C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Mapping signed - unsigned", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Codifica interi con segno (complemento a due)" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Estensione della rappresentazione binaria di un numero intero". Durante la spiegazione, conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Mapping signed - unsigned", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Estensione rappresentazione binaria di un numero intero" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md, sezione "Mapping signed - unsigned" (../README.md#mapping-signed---unsigned). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#estensione-rappresentazione-binaria-di-un-numero-intero">Estensione rappresentazione binaria di un numero intero</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su bit, byte, basi numeriche e interpretazione dei dati in memoria. Si collega al blocco superiore Rappresentazione delle informazioni. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Estensione della rappresentazione binaria di un numero intero" lo studente dovrebbe aver seguito il lavoro precedente su "Mapping signed - unsigned", sapere come compilare ed eseguire piccoli programmi in C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Estensione e rappresentazione binaria di un numero intero", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Mapping signed - unsigned" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Troncamento e rappresentazione binaria di un numero". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Estensione rappresentazione binaria di un numero intero", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Troncamento rappresentazione binaria di un numero" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md, sezione "Estensione rappresentazione binaria di un numero intero" (../README.md#estensione-rappresentazione-binaria-di-un-numero-intero). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#troncamento-rappresentazione-binaria-di-un-numero">Troncamento rappresentazione binaria di un numero</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su bit, byte, basi numeriche e interpretazione dei dati in memoria. Si collega al blocco superiore "Rappresentazione delle informazioni". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Troncamento rappresentazione binaria di un numero", lo studente dovrebbe aver seguito il lavoro precedente su "Estensione rappresentazione binaria di un numero intero", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione, lo studente deve sapere spiegare il ruolo di "Troncamento rappresentazione binaria di un numero", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Estensione rappresentazione binaria di un numero intero" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Addizione senza segno". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Troncamento della rappresentazione binaria di un numero", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Addizione senza segno" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md, sezione "Troncamento rappresentazione binaria di un numero" (../README.md#troncamento-rappresentazione-binaria-di-un-numero). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#addizione-senza-segno">Addizione senza segno</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sul concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore "Rappresentazione delle informazioni". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Addizione senza segno", lo studente dovrebbe aver seguito il lavoro precedente su "Troncamento rappresentazione binaria di un numero", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Addizione senza segno", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Troncamento rappresentazione binaria di un numero" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Addizione con segno". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Addizione senza segno", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Addizione con segno" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md, sezione "Addizione senza segno" (../README.md#addizione-senza-segno). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#addizione-con-segno">Addizione con segno</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sul concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore "Rappresentazione delle informazioni". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Addizione con segno", lo studente dovrebbe aver seguito il lavoro precedente su "Addizione senza segno", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Addizione con segno", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Addizione senza segno" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Tipi di dato". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Addizione con segno", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Tipi di dato" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md, sezione "Addizione con segno" (../README.md#addizione-con-segno). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#tipi-di-dato">Tipi di dato</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su tipi primitivi del C, dimensioni, range e scelta del tipo corretto. Si collega al blocco superiore "Rappresentazione delle informazioni". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Tipi di dato", lo studente dovrebbe aver seguito il lavoro precedente su "Addizione con segno", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione, lo studente deve sapere spiegare il ruolo di "Tipi di dato", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Addizione con segno" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "`int`". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Tipi di dato", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "`int`" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md, sezione "Tipi di dato" (../README.md#tipi-di-dato). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#int">`int`</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per il Terzo anno. Serve a lavorare sul concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore "Rappresentazione delle informazioni". I sottoparagrafi collegati sono: Stampare `int`, Altri tipi interi, Stampare altri tipi di interi, Overflow `int`. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare `int`, lo studente dovrebbe aver seguito il lavoro precedente su "Tipi di dato", sapere come compilare ed eseguire piccoli programmi C, saper leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione, lo studente deve saper spiegare il ruolo di "`int`", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Tipi di dato" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Stampare `int`". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "`int`", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Stampare `int`" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "`int`" (../README.md#int). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    - <details>
      <summary><a href="../README.md#stampare-int">Stampare `int`</a> <code>README.md</code> H4 <code>draft</code></summary>

      - <details>
        <summary><strong>Cornice didattica</strong></summary>

        - <details>
          <summary><strong>Contesto</strong></summary>

          Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Rappresentazione delle informazioni > `int`. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
          </details>
        - <details>
          <summary><strong>Prerequisiti</strong></summary>

          Prima di affrontare "Stampare `int`" lo studente dovrebbe aver seguito il lavoro precedente su "`int`", sapere come compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
          </details>
        - <details>
          <summary><strong>Obiettivi</strong></summary>

          Alla fine della lezione lo studente deve saper spiegare il ruolo di "Stampare `int`", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
          </details>
        - <details>
          <summary><strong>Richiamo</strong></summary>

          Richiama il passaggio precedente su "`int`" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
          </details>
        - <details>
          <summary><strong>Anticipazione</strong></summary>

          Questo argomento prepara il lavoro successivo su "Altri tipi interi". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, lasciando già una mappa mentale del percorso.
          </details>
        - <details>
          <summary><strong>Prossimo passo</strong></summary>

          Dopo la spiegazione, proponi un esempio minimo su "Stampare `int`", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Altri tipi interi" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
          </details>
        - <details>
          <summary><strong>Rimando</strong></summary>

          Riferimento principale: README.md sezione "Stampare `int`" (../README.md#stampare-int). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
          </details>
        </details>
      </details>
    - <details>
      <summary><a href="../README.md#altri-tipi-interi">Altri tipi interi</a> <code>README.md</code> H4 <code>draft</code></summary>

      - <details>
        <summary><strong>Cornice didattica</strong></summary>

        - <details>
          <summary><strong>Contesto</strong></summary>

          Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su tipi primitivi del C, dimensioni, range e scelta del tipo corretto. Si collega al blocco superiore Rappresentazione delle informazioni > `int`. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
          </details>
        - <details>
          <summary><strong>Prerequisiti</strong></summary>

          Prima di affrontare "Altri tipi interi", lo studente dovrebbe aver seguito il lavoro precedente su "Stampare `int`", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
          </details>
        - <details>
          <summary><strong>Obiettivi</strong></summary>

          Alla fine della lezione lo studente deve sapere spiegare il ruolo di "Altri tipi interi", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
          </details>
        - <details>
          <summary><strong>Richiamo</strong></summary>

          Richiama il passaggio precedente su "Stampare `int`" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
          </details>
        - <details>
          <summary><strong>Anticipazione</strong></summary>

          Questo argomento prepara il lavoro successivo su "Stampare altri tipi di interi". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
          </details>
        - <details>
          <summary><strong>Prossimo passo</strong></summary>

          Dopo la spiegazione, proponi un esempio minimo su "Altri tipi interi", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Stampare altri tipi di interi" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
          </details>
        - <details>
          <summary><strong>Rimando</strong></summary>

          Riferimento principale: README.md, sezione "Altri tipi interi" (../README.md#altri-tipi-interi). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
          </details>
        </details>
      </details>
    - <details>
      <summary><a href="../README.md#stampare-altri-tipi-di-interi">Stampare altri tipi di interi</a> <code>README.md</code> H4 <code>draft</code></summary>

      - <details>
        <summary><strong>Cornice didattica</strong></summary>

        - <details>
          <summary><strong>Contesto</strong></summary>

          Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su tipi primitivi del C, dimensioni, range e scelta del tipo corretto. Si collega al blocco superiore Rappresentazione delle informazioni > `int`. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
          </details>
        - <details>
          <summary><strong>Prerequisiti</strong></summary>

          Prima di affrontare "Stampare altri tipi di interi" lo studente dovrebbe aver seguito il lavoro precedente su "Altri tipi interi", saper compilare ed eseguire piccoli programmi in C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
          </details>
        - <details>
          <summary><strong>Obiettivi</strong></summary>

          Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Stampare altri tipi di interi", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
          </details>
        - <details>
          <summary><strong>Richiamo</strong></summary>

          Richiama il passaggio precedente su "Altri tipi interi" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
          </details>
        - <details>
          <summary><strong>Anticipazione</strong></summary>

          Questo argomento prepara il lavoro successivo su "Overflow `int`". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
          </details>
        - <details>
          <summary><strong>Prossimo passo</strong></summary>

          Dopo la spiegazione, proponi un esempio minimo su "Stampare altri tipi di interi", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Overflow `int`" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
          </details>
        - <details>
          <summary><strong>Rimando</strong></summary>

          Riferimento principale: README.md, sezione "Stampare altri tipi di interi" (../README.md#stampare-altri-tipi-di-interi). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
          </details>
        </details>
      </details>
    - <details>
      <summary><a href="../README.md#overflow-int">Overflow `int`</a> <code>README.md</code> H4 <code>draft</code></summary>

      - <details>
        <summary><strong>Cornice didattica</strong></summary>

        - <details>
          <summary><strong>Contesto</strong></summary>

          Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sul concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore "Rappresentazione delle informazioni" > `int`. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
          </details>
        - <details>
          <summary><strong>Prerequisiti</strong></summary>

          Prima di affrontare "Overflow `int`" lo studente dovrebbe aver seguito il lavoro precedente su "Stampare altri tipi di interi", sapere come compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
          </details>
        - <details>
          <summary><strong>Obiettivi</strong></summary>

          Alla fine della lezione lo studente deve sapere spiegare il ruolo di "Overflow `int`", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
          </details>
        - <details>
          <summary><strong>Richiamo</strong></summary>

          Richiama il passaggio precedente su "Stampare altri tipi di interi" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
          </details>
        - <details>
          <summary><strong>Anticipazione</strong></summary>

          Questo argomento prepara il lavoro successivo su "`char`". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
          </details>
        - <details>
          <summary><strong>Prossimo passo</strong></summary>

          Dopo la spiegazione, proponi un esempio minimo su "Overflow `int`", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "`char`" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
          </details>
        - <details>
          <summary><strong>Rimando</strong></summary>

          Riferimento principale: README.md, sezione "Overflow `int`" (../README.md#overflow-int). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
          </details>
        </details>
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#char">`char`</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "`char`" lo studente dovrebbe aver seguito il lavoro precedente su "Overflow `int`", sapere come compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione, lo studente deve saper spiegare il ruolo di "`char`", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Overflow `int`" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Stampare un `char`". Durante la spiegazione, conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "`char`", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Stampare un `char`" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md, sezione "`char`" (../README.md#char). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#stampare-un-char">Stampare un `char`</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sul concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Stampare un `char`", lo studente dovrebbe aver seguito il lavoro precedente su "`char`", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione, lo studente deve sapere spiegare il ruolo di "Stampare un `char`", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "`char`" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Costanti". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Stampare un `char`", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Costanti" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md, sezione "Stampare un `char`" (../README.md#stampare-un-char). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#costanti">Costanti</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Costanti", lo studente dovrebbe aver seguito il lavoro precedente su "Stampare un `char`", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Costanti", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Stampare un `char`" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Operatori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Costanti", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Operatori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Costanti" (../README.md#costanti). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-2 - Operatori, condizioni e selezione

<details>
<summary><strong>Apri contenuto UDA - Base - 3 settimane</strong></summary>

- Percorso: `Base`
- Settimane: `3`

#### Argomenti

- <details>
  <summary><a href="../README.md#operatori">Operatori</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su operatori aritmetici, logici, relazionali e loro precedenza. I sottoparagrafi collegati sono: Operatore di assegnamento: =. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Operatori" lo studente dovrebbe aver seguito il lavoro precedente su "Costanti", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Costanti" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Operatore di assegnamento: =". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Operatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore di assegnamento: =" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Operatori" (../README.md#operatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#operatore-di-assegnamento">Operatore di assegnamento: =</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Operatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Operatore di assegnamento: =" lo studente dovrebbe aver seguito il lavoro precedente su "Operatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore di assegnamento: =", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Operatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Operatore somma: +". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Operatore di assegnamento: =", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore somma: +" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Operatore di assegnamento: =" (../README.md#operatore-di-assegnamento). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#operatore-somma">Operatore somma: +</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Operatore somma: +" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore di assegnamento: =", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore somma: +", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Operatore di assegnamento: =" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Operatore differenza: -". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Operatore somma: +", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore differenza: -" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Operatore somma: +" (../README.md#operatore-somma). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#operatore-differenza">Operatore differenza: -</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Operatore differenza: -" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore somma: +", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore differenza: -", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Operatore somma: +" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Operatore segno: - e +". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Operatore differenza: -", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore segno: - e +" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Operatore differenza: -" (../README.md#operatore-differenza). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#operatore-segno---e">Operatore segno: - e +</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Operatore segno: - e +" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore differenza: -", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore segno: - e +", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Operatore differenza: -" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Operatore moltiplicazione: *". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Operatore segno: - e +", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore moltiplicazione: *" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Operatore segno: - e +" (../README.md#operatore-segno---e). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#operatore-moltiplicazione">Operatore moltiplicazione: *</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Operatore moltiplicazione: *" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore segno: - e +", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore moltiplicazione: *", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Operatore segno: - e +" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Operatore divisione: /". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Operatore moltiplicazione: *", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore divisione: /" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Operatore moltiplicazione: *" (../README.md#operatore-moltiplicazione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#operatore-divisione">Operatore divisione: /</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Operatore divisione: /" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore moltiplicazione: *", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore divisione: /", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Operatore moltiplicazione: *" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Operatore %". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Operatore divisione: /", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore %" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Operatore divisione: /" (../README.md#operatore-divisione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#operatore">Operatore %</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Operatore %" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore divisione: /", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore %", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Operatore divisione: /" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Operatore incremento/decremento ++ --". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Operatore %", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore incremento/decremento ++ --" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Operatore %" (../README.md#operatore). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#operatore-incrementodecremento">Operatore incremento/decremento ++ --</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Operatore incremento/decremento ++ --" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore %", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore incremento/decremento ++ --", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Operatore %" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Operatore `sizeof`". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Operatore incremento/decremento ++ --", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore `sizeof`" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Operatore incremento/decremento ++ --" (../README.md#operatore-incrementodecremento). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#operatore-sizeof">Operatore `sizeof`</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Operatore `sizeof`" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore incremento/decremento ++ --", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore `sizeof`", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Operatore incremento/decremento ++ --" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Cast". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Operatore `sizeof`", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Cast" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Operatore `sizeof`" (../README.md#operatore-sizeof). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#cast">Cast</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. I sottoparagrafi collegati sono: Cast tra `signed` e `unsigned`. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Cast" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore `sizeof`", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Cast", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Operatore `sizeof`" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Cast tra `signed` e `unsigned`". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Cast", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Cast tra `signed` e `unsigned`" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Cast" (../README.md#cast). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#cast-tra-signed-e-unsigned">Cast tra `signed` e `unsigned`</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su numeri con segno, complemento a due, range e casi limite. Si collega al blocco superiore Cast. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Cast tra `signed` e `unsigned`" lo studente dovrebbe aver seguito il lavoro precedente su "Cast", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Cast tra `signed` e `unsigned`", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Cast" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Controllo del flusso". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Cast tra `signed` e `unsigned`", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Controllo del flusso" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Cast tra `signed` e `unsigned`" (../README.md#cast-tra-signed-e-unsigned). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#controllo-del-flusso">Controllo del flusso</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su if, switch, cicli e costruzione del flusso di esecuzione. I sottoparagrafi collegati sono: if o if-else, Condizioni complesse con l'uso di operatori logici e condizionali, for, while, do-while, switch, break e continue. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Controllo del flusso" lo studente dovrebbe aver seguito il lavoro precedente su "Cast tra `signed` e `unsigned`", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Controllo del flusso", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Cast tra `signed` e `unsigned`" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "if o if-else". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Controllo del flusso", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "if o if-else" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Controllo del flusso" (../README.md#controllo-del-flusso). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#if-o-if-else">if o if-else</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "if o if-else" lo studente dovrebbe aver seguito il lavoro precedente su "Controllo del flusso", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "if o if-else", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Controllo del flusso" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Condizioni complesse con l'uso di operatori logici e condizionali". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "if o if-else", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Condizioni complesse con l'uso di operatori logici e condizionali" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "if o if-else" (../README.md#if-o-if-else). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#condizioni-complesse-con-luso-di-operatori-logici-e-condizionali">Condizioni complesse con l'uso di operatori logici e condizionali</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su operatori aritmetici, logici, relazionali e loro precedenza. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Condizioni complesse con l'uso di operatori logici e condizionali" lo studente dovrebbe aver seguito il lavoro precedente su "if o if-else", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Condizioni complesse con l'uso di operatori logici e condizionali", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "if o if-else" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "for". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Condizioni complesse con l'uso di operatori logici e condizionali", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "for" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Condizioni complesse con l'uso di operatori logici e condizionali" (../README.md#condizioni-complesse-con-luso-di-operatori-logici-e-condizionali). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#for">for</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "for" lo studente dovrebbe aver seguito il lavoro precedente su "Condizioni complesse con l'uso di operatori logici e condizionali", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "for", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Condizioni complesse con l'uso di operatori logici e condizionali" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "while". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "for", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "while" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "for" (../README.md#for). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#while">while</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "while" lo studente dovrebbe aver seguito il lavoro precedente su "for", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "while", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "for" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "do-while". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "while", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "do-while" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "while" (../README.md#while). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#do-while">do-while</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "do-while" lo studente dovrebbe aver seguito il lavoro precedente su "while", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "do-while", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "while" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "switch". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "do-while", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "switch" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "do-while" (../README.md#do-while). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#switch">switch</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "switch" lo studente dovrebbe aver seguito il lavoro precedente su "do-while", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "switch", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "do-while" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "break e continue". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "switch", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "break e continue" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "switch" (../README.md#switch). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#break-e-continue">break e continue</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "break e continue" lo studente dovrebbe aver seguito il lavoro precedente su "switch", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "break e continue", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "switch" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "break e continue", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "break e continue" (../README.md#break-e-continue). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  </details>

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-3 - Cicli e funzioni

<details>
<summary><strong>Apri contenuto UDA - Base - 4 settimane</strong></summary>

- Percorso: `Base`
- Settimane: `4`

#### Argomenti

- <details>
  <summary><a href="../README.md#funzioni-1">Funzioni</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Cicli e funzioni" del percorso Base per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "break e continue", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "break e continue" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Dichiarazione di funzione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Dichiarazione di funzione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Funzioni" (../README.md#funzioni-1). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#dichiarazione-di-funzione">Dichiarazione di funzione</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Cicli e funzioni" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Dichiarazione di funzione" lo studente dovrebbe aver seguito il lavoro precedente su "Funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Dichiarazione di funzione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Uso di void nelle funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Dichiarazione di funzione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Uso di void nelle funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Dichiarazione di funzione" (../README.md#dichiarazione-di-funzione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#uso-di-void-nelle-funzioni">Uso di void nelle funzioni</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Cicli e funzioni" del percorso Base per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Uso di void nelle funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Dichiarazione di funzione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Uso di void nelle funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Dichiarazione di funzione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Definizione di funzione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Uso di void nelle funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Definizione di funzione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Uso di void nelle funzioni" (../README.md#uso-di-void-nelle-funzioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#definizione-di-funzione">Definizione di funzione</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Cicli e funzioni" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Definizione di funzione" lo studente dovrebbe aver seguito il lavoro precedente su "Uso di void nelle funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Definizione di funzione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Uso di void nelle funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Chiamata di funzione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Definizione di funzione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Chiamata di funzione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Definizione di funzione" (../README.md#definizione-di-funzione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#chiamata-di-funzione">Chiamata di funzione</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Cicli e funzioni" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Chiamata di funzione" lo studente dovrebbe aver seguito il lavoro precedente su "Definizione di funzione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Chiamata di funzione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Definizione di funzione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Passaggio di parametri per valore". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Chiamata di funzione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Passaggio di parametri per valore" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Chiamata di funzione" (../README.md#chiamata-di-funzione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#passaggio-di-parametri-per-valore">Passaggio di parametri per valore</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Cicli e funzioni" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Passaggio di parametri per valore" lo studente dovrebbe aver seguito il lavoro precedente su "Chiamata di funzione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Passaggio di parametri per valore", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Chiamata di funzione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Vettori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Passaggio di parametri per valore", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Vettori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Passaggio di parametri per valore" (../README.md#passaggio-di-parametri-per-valore). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-4 - Array e stringhe semplici

<details>
<summary><strong>Apri contenuto UDA - Base - 4 settimane</strong></summary>

- Percorso: `Base`
- Settimane: `4`

#### Argomenti

- <details>
  <summary><a href="../README.md#vettori">Vettori</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Array e stringhe semplici" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. I sottoparagrafi collegati sono: Inizializzare un vettore, Dimensione vettore (`sizeof`). La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Vettori" lo studente dovrebbe aver seguito il lavoro precedente su "Passaggio di parametri per valore", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Vettori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Passaggio di parametri per valore" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Inizializzare un vettore". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Vettori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Inizializzare un vettore" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Vettori" (../README.md#vettori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#inizializzare-un-vettore">Inizializzare un vettore</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Array e stringhe semplici" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Vettori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Inizializzare un vettore" lo studente dovrebbe aver seguito il lavoro precedente su "Vettori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Inizializzare un vettore", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Vettori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Dimensione vettore (`sizeof`)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Inizializzare un vettore", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Dimensione vettore (`sizeof`)" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Inizializzare un vettore" (../README.md#inizializzare-un-vettore). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#dimensione-vettore-sizeof">Dimensione vettore (`sizeof`)</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Array e stringhe semplici" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Vettori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Dimensione vettore (`sizeof`)" lo studente dovrebbe aver seguito il lavoro precedente su "Inizializzare un vettore", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Dimensione vettore (`sizeof`)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Inizializzare un vettore" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Le stringhe". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Dimensione vettore (`sizeof`)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Le stringhe" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Dimensione vettore (`sizeof`)" (../README.md#dimensione-vettore-sizeof). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#le-stringhe">Le stringhe</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Array e stringhe semplici" del percorso Base per Terzo anno. Serve a lavorare su array di char terminati da carattere nullo e funzioni di libreria associate. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Le stringhe" lo studente dovrebbe aver seguito il lavoro precedente su "Dimensione vettore (`sizeof`)", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Le stringhe", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Dimensione vettore (`sizeof`)" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Dettagli sull'inizializzazione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Le stringhe", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Dettagli sull'inizializzazione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Le stringhe" (../README.md#le-stringhe). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#dettagli-sullinizializzazione">Dettagli sull'inizializzazione</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Array e stringhe semplici" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Dettagli sull'inizializzazione" lo studente dovrebbe aver seguito il lavoro precedente su "Le stringhe", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Dettagli sull'inizializzazione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Le stringhe" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Stampare una stringa". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Dettagli sull'inizializzazione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Stampare una stringa" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Dettagli sull'inizializzazione" (../README.md#dettagli-sullinizializzazione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#stampare-una-stringa">Stampare una stringa</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Array e stringhe semplici" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Stampare una stringa" lo studente dovrebbe aver seguito il lavoro precedente su "Dettagli sull'inizializzazione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Stampare una stringa", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Dettagli sull'inizializzazione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Array come parametri a funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Stampare una stringa", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Array come parametri a funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Stampare una stringa" (../README.md#stampare-una-stringa). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#array-come-parametri-a-funzioni">Array come parametri a funzioni</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Array e stringhe semplici" del percorso Base per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Array come parametri a funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Stampare una stringa", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Array come parametri a funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Stampare una stringa" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Le strutture". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Array come parametri a funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Le strutture" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Array come parametri a funzioni" (../README.md#array-come-parametri-a-funzioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-5 - Struct e consolidamento

<details>
<summary><strong>Apri contenuto UDA - Base - 3 settimane</strong></summary>

- Percorso: `Base`
- Settimane: `3`

#### Argomenti

- <details>
  <summary><a href="../README.md#le-strutture">Le strutture</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Struct e consolidamento" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. I sottoparagrafi collegati sono: Passaggio di strutture a funzioni. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Le strutture" lo studente dovrebbe aver seguito il lavoro precedente su "Array come parametri a funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Le strutture", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Array come parametri a funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Passaggio di strutture a funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Le strutture", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Passaggio di strutture a funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Le strutture" (../README.md#le-strutture). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#passaggio-di-strutture-a-funzioni">Passaggio di strutture a funzioni</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Struct e consolidamento" del percorso Base per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. Si collega al blocco superiore Le strutture. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Passaggio di strutture a funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Le strutture", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Passaggio di strutture a funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Le strutture" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Array bidimensionali". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Passaggio di strutture a funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Array bidimensionali" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Passaggio di strutture a funzioni" (../README.md#passaggio-di-strutture-a-funzioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#array-bidimensionali">Array bidimensionali</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Struct e consolidamento" del percorso Base per Terzo anno. Serve a lavorare su sequenze contigue di elementi, indici, dimensione e accesso in memoria. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Array bidimensionali" lo studente dovrebbe aver seguito il lavoro precedente su "Passaggio di strutture a funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Array bidimensionali", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Passaggio di strutture a funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "I puntatori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Array bidimensionali", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "I puntatori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Array bidimensionali" (../README.md#array-bidimensionali). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-6 - Puntatori, array e indirizzi

<details>
<summary><strong>Apri contenuto UDA - Intermedio - 4 settimane</strong></summary>

- Percorso: `Intermedio`
- Settimane: `4`

#### Argomenti

- <details>
  <summary><a href="../README.md#i-puntatori">I puntatori</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su indirizzi, dereferenziazione, aritmetica dei puntatori e relazione con gli array. I sottoparagrafi collegati sono: Puntatori non inizializzati, Il puntatore nullo (NULL), Vettori, Relazione tra array e puntatori, Differenza tra puntatori, Le stringhe, Dettagli sull'inizializzazione, Stampare una stringa, Funzioni, Dichiarazione di funzione, Uso di void nelle funzioni, Definizione di funzione, Chiamata di funzione, Passaggio di parametri per valore, Passaggio di parametri per indirizzo, Passaggio di puntatori const, Array come parametri a funzioni, Allocazione dinamica della memoria, Array bidimensionali, Array di puntatori, Differenza tra array bidimensionali e array di puntatori, Sezioni di memoria di un programma C, L'inizializzazione delle variabili, Allocazione dinamica di matrici, Le strutture. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "I puntatori" lo studente dovrebbe aver seguito il lavoro precedente su "Array bidimensionali", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "I puntatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Array bidimensionali" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Puntatori non inizializzati". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "I puntatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Puntatori non inizializzati" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "I puntatori" (../README.md#i-puntatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#puntatori-non-inizializzati">Puntatori non inizializzati</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su indirizzi, dereferenziazione, aritmetica dei puntatori e relazione con gli array. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Puntatori non inizializzati" lo studente dovrebbe aver seguito il lavoro precedente su "I puntatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Puntatori non inizializzati", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "I puntatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Il puntatore nullo (NULL)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Puntatori non inizializzati", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Il puntatore nullo (NULL)" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Puntatori non inizializzati" (../README.md#puntatori-non-inizializzati). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#il-puntatore-nullo-null">Il puntatore nullo (NULL)</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. I sottoparagrafi collegati sono: Aritmetica puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Il puntatore nullo (NULL)" lo studente dovrebbe aver seguito il lavoro precedente su "Puntatori non inizializzati", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Il puntatore nullo (NULL)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Puntatori non inizializzati" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Aritmetica puntatori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Il puntatore nullo (NULL)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Aritmetica puntatori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Il puntatore nullo (NULL)" (../README.md#il-puntatore-nullo-null). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    - <details>
      <summary><a href="../README.md#aritmetica-puntatori">Aritmetica puntatori</a> <code>README.md</code> H4 <code>draft</code></summary>

      - <details>
        <summary><strong>Cornice didattica</strong></summary>

        - <details>
          <summary><strong>Contesto</strong></summary>

          Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su indirizzi, dereferenziazione, aritmetica dei puntatori e relazione con gli array. Si collega al blocco superiore I puntatori > Il puntatore nullo (NULL). La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
          </details>
        - <details>
          <summary><strong>Prerequisiti</strong></summary>

          Prima di affrontare "Aritmetica puntatori" lo studente dovrebbe aver seguito il lavoro precedente su "Il puntatore nullo (NULL)", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
          </details>
        - <details>
          <summary><strong>Obiettivi</strong></summary>

          Alla fine della lezione lo studente deve saper spiegare il ruolo di "Aritmetica puntatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
          </details>
        - <details>
          <summary><strong>Richiamo</strong></summary>

          Richiama il passaggio precedente su "Il puntatore nullo (NULL)" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
          </details>
        - <details>
          <summary><strong>Anticipazione</strong></summary>

          Questo argomento prepara il lavoro successivo su "Vettori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
          </details>
        - <details>
          <summary><strong>Prossimo passo</strong></summary>

          Dopo la spiegazione, proponi un esempio minimo su "Aritmetica puntatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Vettori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
          </details>
        - <details>
          <summary><strong>Rimando</strong></summary>

          Riferimento principale: README.md sezione "Aritmetica puntatori" (../README.md#aritmetica-puntatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
          </details>
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#vettori">Vettori</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. I sottoparagrafi collegati sono: Inizializzare un vettore, Dimensione vettore (`sizeof`). La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Vettori" lo studente dovrebbe aver seguito il lavoro precedente su "Aritmetica puntatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Vettori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Aritmetica puntatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Inizializzare un vettore". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Vettori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Inizializzare un vettore" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Vettori" (../README.md#vettori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    - <details>
      <summary><a href="../README.md#inizializzare-un-vettore">Inizializzare un vettore</a> <code>README.md</code> H4 <code>draft</code></summary>

      - <details>
        <summary><strong>Cornice didattica</strong></summary>

        - <details>
          <summary><strong>Contesto</strong></summary>

          Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori > Vettori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
          </details>
        - <details>
          <summary><strong>Prerequisiti</strong></summary>

          Prima di affrontare "Inizializzare un vettore" lo studente dovrebbe aver seguito il lavoro precedente su "Vettori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
          </details>
        - <details>
          <summary><strong>Obiettivi</strong></summary>

          Alla fine della lezione lo studente deve saper spiegare il ruolo di "Inizializzare un vettore", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
          </details>
        - <details>
          <summary><strong>Richiamo</strong></summary>

          Richiama il passaggio precedente su "Vettori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
          </details>
        - <details>
          <summary><strong>Anticipazione</strong></summary>

          Questo argomento prepara il lavoro successivo su "Dimensione vettore (`sizeof`)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
          </details>
        - <details>
          <summary><strong>Prossimo passo</strong></summary>

          Dopo la spiegazione, proponi un esempio minimo su "Inizializzare un vettore", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Dimensione vettore (`sizeof`)" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
          </details>
        - <details>
          <summary><strong>Rimando</strong></summary>

          Riferimento principale: README.md sezione "Inizializzare un vettore" (../README.md#inizializzare-un-vettore). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
          </details>
        </details>
      </details>
    - <details>
      <summary><a href="../README.md#dimensione-vettore-sizeof">Dimensione vettore (`sizeof`)</a> <code>README.md</code> H4 <code>draft</code></summary>

      - <details>
        <summary><strong>Cornice didattica</strong></summary>

        - <details>
          <summary><strong>Contesto</strong></summary>

          Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori > Vettori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
          </details>
        - <details>
          <summary><strong>Prerequisiti</strong></summary>

          Prima di affrontare "Dimensione vettore (`sizeof`)" lo studente dovrebbe aver seguito il lavoro precedente su "Inizializzare un vettore", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
          </details>
        - <details>
          <summary><strong>Obiettivi</strong></summary>

          Alla fine della lezione lo studente deve saper spiegare il ruolo di "Dimensione vettore (`sizeof`)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
          </details>
        - <details>
          <summary><strong>Richiamo</strong></summary>

          Richiama il passaggio precedente su "Inizializzare un vettore" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
          </details>
        - <details>
          <summary><strong>Anticipazione</strong></summary>

          Questo argomento prepara il lavoro successivo su "Relazione tra array e puntatori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
          </details>
        - <details>
          <summary><strong>Prossimo passo</strong></summary>

          Dopo la spiegazione, proponi un esempio minimo su "Dimensione vettore (`sizeof`)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Relazione tra array e puntatori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
          </details>
        - <details>
          <summary><strong>Rimando</strong></summary>

          Riferimento principale: README.md sezione "Dimensione vettore (`sizeof`)" (../README.md#dimensione-vettore-sizeof). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
          </details>
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#relazione-tra-array-e-puntatori">Relazione tra array e puntatori</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su sequenze contigue di elementi, indici, dimensione e accesso in memoria. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Relazione tra array e puntatori" lo studente dovrebbe aver seguito il lavoro precedente su "Dimensione vettore (`sizeof`)", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Relazione tra array e puntatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Dimensione vettore (`sizeof`)" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Differenza tra puntatori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Relazione tra array e puntatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Differenza tra puntatori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Relazione tra array e puntatori" (../README.md#relazione-tra-array-e-puntatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#differenza-tra-puntatori">Differenza tra puntatori</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su indirizzi, dereferenziazione, aritmetica dei puntatori e relazione con gli array. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Differenza tra puntatori" lo studente dovrebbe aver seguito il lavoro precedente su "Relazione tra array e puntatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Differenza tra puntatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Relazione tra array e puntatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Le stringhe". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Differenza tra puntatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Le stringhe" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Differenza tra puntatori" (../README.md#differenza-tra-puntatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#le-stringhe">Le stringhe</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su array di char terminati da carattere nullo e funzioni di libreria associate. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Le stringhe" lo studente dovrebbe aver seguito il lavoro precedente su "Differenza tra puntatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Le stringhe", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Differenza tra puntatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Dettagli sull'inizializzazione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Le stringhe", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Dettagli sull'inizializzazione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Le stringhe" (../README.md#le-stringhe). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#dettagli-sullinizializzazione">Dettagli sull'inizializzazione</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Dettagli sull'inizializzazione" lo studente dovrebbe aver seguito il lavoro precedente su "Le stringhe", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Dettagli sull'inizializzazione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Le stringhe" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Stampare una stringa". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Dettagli sull'inizializzazione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Stampare una stringa" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Dettagli sull'inizializzazione" (../README.md#dettagli-sullinizializzazione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#stampare-una-stringa">Stampare una stringa</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Stampare una stringa" lo studente dovrebbe aver seguito il lavoro precedente su "Dettagli sull'inizializzazione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Stampare una stringa", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Dettagli sull'inizializzazione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Stampare una stringa", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Stampare una stringa" (../README.md#stampare-una-stringa). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#funzioni-1">Funzioni</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Stampare una stringa", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Stampare una stringa" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Dichiarazione di funzione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Dichiarazione di funzione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Funzioni" (../README.md#funzioni-1). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#dichiarazione-di-funzione">Dichiarazione di funzione</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Dichiarazione di funzione" lo studente dovrebbe aver seguito il lavoro precedente su "Funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Dichiarazione di funzione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Uso di void nelle funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Dichiarazione di funzione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Uso di void nelle funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Dichiarazione di funzione" (../README.md#dichiarazione-di-funzione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#uso-di-void-nelle-funzioni">Uso di void nelle funzioni</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Uso di void nelle funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Dichiarazione di funzione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Uso di void nelle funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Dichiarazione di funzione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Definizione di funzione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Uso di void nelle funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Definizione di funzione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Uso di void nelle funzioni" (../README.md#uso-di-void-nelle-funzioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#definizione-di-funzione">Definizione di funzione</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Definizione di funzione" lo studente dovrebbe aver seguito il lavoro precedente su "Uso di void nelle funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Definizione di funzione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Uso di void nelle funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Chiamata di funzione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Definizione di funzione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Chiamata di funzione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Definizione di funzione" (../README.md#definizione-di-funzione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#chiamata-di-funzione">Chiamata di funzione</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Chiamata di funzione" lo studente dovrebbe aver seguito il lavoro precedente su "Definizione di funzione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Chiamata di funzione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Definizione di funzione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Passaggio di parametri per valore". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Chiamata di funzione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Passaggio di parametri per valore" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Chiamata di funzione" (../README.md#chiamata-di-funzione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#passaggio-di-parametri-per-valore">Passaggio di parametri per valore</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Passaggio di parametri per valore" lo studente dovrebbe aver seguito il lavoro precedente su "Chiamata di funzione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Passaggio di parametri per valore", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Chiamata di funzione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Passaggio di parametri per indirizzo". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Passaggio di parametri per valore", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Passaggio di parametri per indirizzo" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Passaggio di parametri per valore" (../README.md#passaggio-di-parametri-per-valore). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#passaggio-di-parametri-per-indirizzo">Passaggio di parametri per indirizzo</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Passaggio di parametri per indirizzo" lo studente dovrebbe aver seguito il lavoro precedente su "Passaggio di parametri per valore", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Passaggio di parametri per indirizzo", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Passaggio di parametri per valore" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Passaggio di puntatori const". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Passaggio di parametri per indirizzo", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Passaggio di puntatori const" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Passaggio di parametri per indirizzo" (../README.md#passaggio-di-parametri-per-indirizzo). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#passaggio-di-puntatori-const">Passaggio di puntatori const</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su indirizzi, dereferenziazione, aritmetica dei puntatori e relazione con gli array. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Passaggio di puntatori const" lo studente dovrebbe aver seguito il lavoro precedente su "Passaggio di parametri per indirizzo", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Passaggio di puntatori const", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Passaggio di parametri per indirizzo" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Array come parametri a funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Passaggio di puntatori const", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Array come parametri a funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Passaggio di puntatori const" (../README.md#passaggio-di-puntatori-const). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#array-come-parametri-a-funzioni">Array come parametri a funzioni</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Array come parametri a funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Passaggio di puntatori const", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Array come parametri a funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Passaggio di puntatori const" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Allocazione dinamica della memoria". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Array come parametri a funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Allocazione dinamica della memoria" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Array come parametri a funzioni" (../README.md#array-come-parametri-a-funzioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#allocazione-dinamica-della-memoria">Allocazione dinamica della memoria</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Allocazione dinamica della memoria" lo studente dovrebbe aver seguito il lavoro precedente su "Array come parametri a funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Allocazione dinamica della memoria", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Array come parametri a funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Array bidimensionali". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Allocazione dinamica della memoria", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Array bidimensionali" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Allocazione dinamica della memoria" (../README.md#allocazione-dinamica-della-memoria). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#array-bidimensionali">Array bidimensionali</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su sequenze contigue di elementi, indici, dimensione e accesso in memoria. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Array bidimensionali" lo studente dovrebbe aver seguito il lavoro precedente su "Allocazione dinamica della memoria", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Array bidimensionali", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Allocazione dinamica della memoria" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Array di puntatori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Array bidimensionali", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Array di puntatori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Array bidimensionali" (../README.md#array-bidimensionali). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#array-di-puntatori">Array di puntatori</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su sequenze contigue di elementi, indici, dimensione e accesso in memoria. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Array di puntatori" lo studente dovrebbe aver seguito il lavoro precedente su "Array bidimensionali", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Array di puntatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Array bidimensionali" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Differenza tra array bidimensionali e array di puntatori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Array di puntatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Differenza tra array bidimensionali e array di puntatori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Array di puntatori" (../README.md#array-di-puntatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#differenza-tra-array-bidimensionali-e-array-di-puntatori">Differenza tra array bidimensionali e array di puntatori</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su sequenze contigue di elementi, indici, dimensione e accesso in memoria. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Differenza tra array bidimensionali e array di puntatori" lo studente dovrebbe aver seguito il lavoro precedente su "Array di puntatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Differenza tra array bidimensionali e array di puntatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Array di puntatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Sezioni di memoria di un programma C". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Differenza tra array bidimensionali e array di puntatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Sezioni di memoria di un programma C" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Differenza tra array bidimensionali e array di puntatori" (../README.md#differenza-tra-array-bidimensionali-e-array-di-puntatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#sezioni-di-memoria-di-un-programma-c">Sezioni di memoria di un programma C</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su struttura minima di un programma C, funzione main, include e stampa a video. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Sezioni di memoria di un programma C" lo studente dovrebbe aver seguito il lavoro precedente su "Differenza tra array bidimensionali e array di puntatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Sezioni di memoria di un programma C", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Differenza tra array bidimensionali e array di puntatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "L'inizializzazione delle variabili". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Sezioni di memoria di un programma C", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "L'inizializzazione delle variabili" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Sezioni di memoria di un programma C" (../README.md#sezioni-di-memoria-di-un-programma-c). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#linizializzazione-delle-variabili">L'inizializzazione delle variabili</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "L'inizializzazione delle variabili" lo studente dovrebbe aver seguito il lavoro precedente su "Sezioni di memoria di un programma C", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "L'inizializzazione delle variabili", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Sezioni di memoria di un programma C" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Allocazione dinamica di matrici". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "L'inizializzazione delle variabili", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Allocazione dinamica di matrici" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "L'inizializzazione delle variabili" (../README.md#linizializzazione-delle-variabili). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#allocazione-dinamica-di-matrici">Allocazione dinamica di matrici</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Allocazione dinamica di matrici" lo studente dovrebbe aver seguito il lavoro precedente su "L'inizializzazione delle variabili", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Allocazione dinamica di matrici", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "L'inizializzazione delle variabili" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Le strutture". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Allocazione dinamica di matrici", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Le strutture" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Allocazione dinamica di matrici" (../README.md#allocazione-dinamica-di-matrici). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#le-strutture">Le strutture</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. I sottoparagrafi collegati sono: Passaggio di strutture a funzioni. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Le strutture" lo studente dovrebbe aver seguito il lavoro precedente su "Allocazione dinamica di matrici", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Le strutture", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Allocazione dinamica di matrici" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Passaggio di strutture a funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Le strutture", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Passaggio di strutture a funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Le strutture" (../README.md#le-strutture). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    - <details>
      <summary><a href="../README.md#passaggio-di-strutture-a-funzioni">Passaggio di strutture a funzioni</a> <code>README.md</code> H4 <code>draft</code></summary>

      - <details>
        <summary><strong>Cornice didattica</strong></summary>

        - <details>
          <summary><strong>Contesto</strong></summary>

          Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. Si collega al blocco superiore I puntatori > Le strutture. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
          </details>
        - <details>
          <summary><strong>Prerequisiti</strong></summary>

          Prima di affrontare "Passaggio di strutture a funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Le strutture", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
          </details>
        - <details>
          <summary><strong>Obiettivi</strong></summary>

          Alla fine della lezione lo studente deve saper spiegare il ruolo di "Passaggio di strutture a funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
          </details>
        - <details>
          <summary><strong>Richiamo</strong></summary>

          Richiama il passaggio precedente su "Le strutture" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
          </details>
        - <details>
          <summary><strong>Anticipazione</strong></summary>

          Questo argomento prepara il lavoro successivo su "Classi di memorizzazione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
          </details>
        - <details>
          <summary><strong>Prossimo passo</strong></summary>

          Dopo la spiegazione, proponi un esempio minimo su "Passaggio di strutture a funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Classi di memorizzazione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
          </details>
        - <details>
          <summary><strong>Rimando</strong></summary>

          Riferimento principale: README.md sezione "Passaggio di strutture a funzioni" (../README.md#passaggio-di-strutture-a-funzioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
          </details>
        </details>
      </details>
    </details>
  </details>

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-7 - Memoria automatica, statica e dinamica

<details>
<summary><strong>Apri contenuto UDA - Intermedio - 4 settimane</strong></summary>

- Percorso: `Intermedio`
- Settimane: `4`

#### Argomenti

- <details>
  <summary><a href="../README.md#classi-di-memorizzazione">Classi di memorizzazione</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su durata, visibilita e collegamento degli identificatori in C. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Classi di memorizzazione" lo studente dovrebbe aver seguito il lavoro precedente su "Passaggio di strutture a funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Classi di memorizzazione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Passaggio di strutture a funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Block scope". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Classi di memorizzazione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Block scope" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Classi di memorizzazione" (../README.md#classi-di-memorizzazione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#block-scope">Block scope</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Block scope" lo studente dovrebbe aver seguito il lavoro precedente su "Classi di memorizzazione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Block scope", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Classi di memorizzazione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "File scope". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Block scope", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "File scope" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Block scope" (../README.md#block-scope). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#file-scope">File scope</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su apertura, lettura, scrittura e chiusura dei file tramite libreria standard C. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "File scope" lo studente dovrebbe aver seguito il lavoro precedente su "Block scope", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "File scope", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Block scope" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Linkage". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "File scope", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Linkage" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "File scope" (../README.md#file-scope). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#linkage">Linkage</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Linkage" lo studente dovrebbe aver seguito il lavoro precedente su "File scope", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Linkage", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "File scope" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Storage duration". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Linkage", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Storage duration" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Linkage" (../README.md#linkage). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#storage-duration">Storage duration</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Storage duration" lo studente dovrebbe aver seguito il lavoro precedente su "Linkage", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Storage duration", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Linkage" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Static storage duration". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Storage duration", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Static storage duration" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Storage duration" (../README.md#storage-duration). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#static-storage-duration">Static storage duration</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Static storage duration" lo studente dovrebbe aver seguito il lavoro precedente su "Storage duration", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Static storage duration", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Storage duration" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Auto storage duration". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Static storage duration", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Auto storage duration" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Static storage duration" (../README.md#static-storage-duration). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#auto-storage-duration">Auto storage duration</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Auto storage duration" lo studente dovrebbe aver seguito il lavoro precedente su "Static storage duration", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Auto storage duration", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Static storage duration" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Classi di memorizzazione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Auto storage duration", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Classi di memorizzazione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Auto storage duration" (../README.md#auto-storage-duration). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#classi-di-memorizzazione-1">Classi di memorizzazione</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su durata, visibilita e collegamento degli identificatori in C. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Classi di memorizzazione" lo studente dovrebbe aver seguito il lavoro precedente su "Auto storage duration", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Classi di memorizzazione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Auto storage duration" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Variabili automatiche (automatic class)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Classi di memorizzazione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Variabili automatiche (automatic class)" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Classi di memorizzazione" (../README.md#classi-di-memorizzazione-1). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#variabili-automatiche-automatic-class">Variabili automatiche (automatic class)</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Variabili automatiche (automatic class)" lo studente dovrebbe aver seguito il lavoro precedente su "Classi di memorizzazione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Variabili automatiche (automatic class)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Classi di memorizzazione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Variabili statiche locali (static variables with block scope)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Variabili automatiche (automatic class)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Variabili statiche locali (static variables with block scope)" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Variabili automatiche (automatic class)" (../README.md#variabili-automatiche-automatic-class). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#variabili-statiche-locali-static-variables-with-block-scope">Variabili statiche locali (static variables with block scope)</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Variabili statiche locali (static variables with block scope)" lo studente dovrebbe aver seguito il lavoro precedente su "Variabili automatiche (automatic class)", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Variabili statiche locali (static variables with block scope)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Variabili automatiche (automatic class)" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Variabili globali con External Linkage (Static variables with External Linkage)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Variabili statiche locali (static variables with block scope)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Variabili globali con External Linkage (Static variables with External Linkage)" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Variabili statiche locali (static variables with block scope)" (../README.md#variabili-statiche-locali-static-variables-with-block-scope). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#variabili-globali-con-external-linkage-static-variables-with-external-linkage">Variabili globali con External Linkage (Static variables with External Linkage)</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Variabili globali con External Linkage (Static variables with External Linkage)" lo studente dovrebbe aver seguito il lavoro precedente su "Variabili statiche locali (static variables with block scope)", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Variabili globali con External Linkage (Static variables with External Linkage)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Variabili statiche locali (static variables with block scope)" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Variabili globali con Internal Linkage (Static variables with Internal Linkage)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Variabili globali con External Linkage (Static variables with External Linkage)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Variabili globali con Internal Linkage (Static variables with Internal Linkage)" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Variabili globali con External Linkage (Static variables with External Linkage)" (../README.md#variabili-globali-con-external-linkage-static-variables-with-external-linkage). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#variabili-globali-con-internal-linkage-static-variables-with-internal-linkage">Variabili globali con Internal Linkage (Static variables with Internal Linkage)</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Variabili globali con Internal Linkage (Static variables with Internal Linkage)" lo studente dovrebbe aver seguito il lavoro precedente su "Variabili globali con External Linkage (Static variables with External Linkage)", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Variabili globali con Internal Linkage (Static variables with Internal Linkage)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Variabili globali con External Linkage (Static variables with External Linkage)" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Differenza tra definizione e dichiarazione di variabile". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Variabili globali con Internal Linkage (Static variables with Internal Linkage)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Differenza tra definizione e dichiarazione di variabile" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Variabili globali con Internal Linkage (Static variables with Internal Linkage)" (../README.md#variabili-globali-con-internal-linkage-static-variables-with-internal-linkage). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#differenza-tra-definizione-e-dichiarazione-di-variabile">Differenza tra definizione e dichiarazione di variabile</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Differenza tra definizione e dichiarazione di variabile" lo studente dovrebbe aver seguito il lavoro precedente su "Variabili globali con Internal Linkage (Static variables with Internal Linkage)", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Differenza tra definizione e dichiarazione di variabile", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Variabili globali con Internal Linkage (Static variables with Internal Linkage)" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Il preprocessore". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Differenza tra definizione e dichiarazione di variabile", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Il preprocessore" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Differenza tra definizione e dichiarazione di variabile" (../README.md#differenza-tra-definizione-e-dichiarazione-di-variabile). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-8 - Preprocessore, header e compilazione separata

<details>
<summary><strong>Apri contenuto UDA - Intermedio - 3 settimane</strong></summary>

- Percorso: `Intermedio`
- Settimane: `3`

#### Argomenti

- <details>
  <summary><a href="../README.md#il-preprocessore">Il preprocessore</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su direttive, macro, inclusione di header e compilazione condizionale. I sottoparagrafi collegati sono: La direttiva #define, La direttiva #include, Le direttive #if #ifdef #ifndef. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Il preprocessore" lo studente dovrebbe aver seguito il lavoro precedente su "Differenza tra definizione e dichiarazione di variabile", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Il preprocessore", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Differenza tra definizione e dichiarazione di variabile" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "La direttiva #define". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Il preprocessore", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "La direttiva #define" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Il preprocessore" (../README.md#il-preprocessore). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#la-direttiva-define">La direttiva #define</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su macro simboliche e sostituzione testuale prima della compilazione. Si collega al blocco superiore Il preprocessore. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "La direttiva #define" lo studente dovrebbe aver seguito il lavoro precedente su "Il preprocessore", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "La direttiva #define", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Il preprocessore" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "La direttiva #include". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "La direttiva #define", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "La direttiva #include" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "La direttiva #define" (../README.md#la-direttiva-define). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#la-direttiva-include">La direttiva #include</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su inclusione di dichiarazioni e separazione tra interfaccia e implementazione. Si collega al blocco superiore Il preprocessore. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "La direttiva #include" lo studente dovrebbe aver seguito il lavoro precedente su "La direttiva #define", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "La direttiva #include", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "La direttiva #define" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Le direttive #if #ifdef #ifndef". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "La direttiva #include", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Le direttive #if #ifdef #ifndef" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "La direttiva #include" (../README.md#la-direttiva-include). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#le-direttive-if-ifdef-ifndef">Le direttive #if #ifdef #ifndef</a> <code>README.md</code> H4 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Il preprocessore. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Le direttive #if #ifdef #ifndef" lo studente dovrebbe aver seguito il lavoro precedente su "La direttiva #include", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Le direttive #if #ifdef #ifndef", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "La direttiva #include" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Eliminazione temporanea di codice". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Le direttive #if #ifdef #ifndef", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Eliminazione temporanea di codice" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Le direttive #if #ifdef #ifndef" (../README.md#le-direttive-if-ifdef-ifndef). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#eliminazione-temporanea-di-codice">Eliminazione temporanea di codice</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Eliminazione temporanea di codice" lo studente dovrebbe aver seguito il lavoro precedente su "Le direttive #if #ifdef #ifndef", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Eliminazione temporanea di codice", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Le direttive #if #ifdef #ifndef" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Protezione del contenuto dei file d'intestazione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Eliminazione temporanea di codice", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Protezione del contenuto dei file d'intestazione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Eliminazione temporanea di codice" (../README.md#eliminazione-temporanea-di-codice). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#protezione-del-contenuto-dei-file-dintestazione">Protezione del contenuto dei file d'intestazione</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su apertura, lettura, scrittura e chiusura dei file tramite libreria standard C. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Protezione del contenuto dei file d'intestazione" lo studente dovrebbe aver seguito il lavoro precedente su "Eliminazione temporanea di codice", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Protezione del contenuto dei file d'intestazione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Eliminazione temporanea di codice" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Suddivisione in moduli di un programma". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Protezione del contenuto dei file d'intestazione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Suddivisione in moduli di un programma" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Protezione del contenuto dei file d'intestazione" (../README.md#protezione-del-contenuto-dei-file-dintestazione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#suddivisione-in-moduli-di-un-programma">Suddivisione in moduli di un programma</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su struttura minima di un programma C, funzione main, include e stampa a video. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Suddivisione in moduli di un programma" lo studente dovrebbe aver seguito il lavoro precedente su "Protezione del contenuto dei file d'intestazione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Suddivisione in moduli di un programma", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Protezione del contenuto dei file d'intestazione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Classi di memorizzazione per le funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Suddivisione in moduli di un programma", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Classi di memorizzazione per le funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Suddivisione in moduli di un programma" (../README.md#suddivisione-in-moduli-di-un-programma). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#classi-di-memorizzazione-per-le-funzioni">Classi di memorizzazione per le funzioni</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Classi di memorizzazione per le funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Suddivisione in moduli di un programma", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Classi di memorizzazione per le funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Suddivisione in moduli di un programma" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Sintassi dichiarazione variabili". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Classi di memorizzazione per le funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Sintassi dichiarazione variabili" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Classi di memorizzazione per le funzioni" (../README.md#classi-di-memorizzazione-per-le-funzioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#sintassi-dichiarazione-variabili">Sintassi dichiarazione variabili</a> <code>README.md</code> H2 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. I sottoparagrafi collegati sono: Classi di memorizzazione per le funzioni, Classi di memorizzazione: riassunto, Suddivisione in moduli di un programma, Il preprocessore, Eliminazione temporanea di codice, Protezione del contenuto dei file d'intestazione. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Sintassi dichiarazione variabili" lo studente dovrebbe aver seguito il lavoro precedente su "Classi di memorizzazione per le funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Sintassi dichiarazione variabili", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Classi di memorizzazione per le funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Classi di memorizzazione per le funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Sintassi dichiarazione variabili", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Classi di memorizzazione per le funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Sintassi dichiarazione variabili" (../README.md#sintassi-dichiarazione-variabili). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#classi-di-memorizzazione-per-le-funzioni">Classi di memorizzazione per le funzioni</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. Si collega al blocco superiore Sintassi dichiarazione variabili. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Classi di memorizzazione per le funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Sintassi dichiarazione variabili", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Classi di memorizzazione per le funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Sintassi dichiarazione variabili" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Classi di memorizzazione: riassunto". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Classi di memorizzazione per le funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Classi di memorizzazione: riassunto" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Classi di memorizzazione per le funzioni" (../README.md#classi-di-memorizzazione-per-le-funzioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#classi-di-memorizzazione-riassunto">Classi di memorizzazione: riassunto</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su durata, visibilita e collegamento degli identificatori in C. Si collega al blocco superiore Sintassi dichiarazione variabili. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Classi di memorizzazione: riassunto" lo studente dovrebbe aver seguito il lavoro precedente su "Classi di memorizzazione per le funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Classi di memorizzazione: riassunto", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Classi di memorizzazione per le funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Suddivisione in moduli di un programma". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Classi di memorizzazione: riassunto", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Suddivisione in moduli di un programma" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Classi di memorizzazione: riassunto" (../README.md#classi-di-memorizzazione-riassunto). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#suddivisione-in-moduli-di-un-programma">Suddivisione in moduli di un programma</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su struttura minima di un programma C, funzione main, include e stampa a video. Si collega al blocco superiore Sintassi dichiarazione variabili. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Suddivisione in moduli di un programma" lo studente dovrebbe aver seguito il lavoro precedente su "Classi di memorizzazione: riassunto", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Suddivisione in moduli di un programma", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Classi di memorizzazione: riassunto" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Il preprocessore". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Suddivisione in moduli di un programma", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Il preprocessore" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Suddivisione in moduli di un programma" (../README.md#suddivisione-in-moduli-di-un-programma). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#il-preprocessore">Il preprocessore</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su direttive, macro, inclusione di header e compilazione condizionale. Si collega al blocco superiore Sintassi dichiarazione variabili. I sottoparagrafi collegati sono: La direttiva #define, La direttiva #include, Le direttive #if #ifdef #ifndef. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Il preprocessore" lo studente dovrebbe aver seguito il lavoro precedente su "Suddivisione in moduli di un programma", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Il preprocessore", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Suddivisione in moduli di un programma" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "La direttiva #define". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Il preprocessore", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "La direttiva #define" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Il preprocessore" (../README.md#il-preprocessore). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    - <details>
      <summary><a href="../README.md#la-direttiva-define">La direttiva #define</a> <code>README.md</code> H4 <code>draft</code></summary>

      - <details>
        <summary><strong>Cornice didattica</strong></summary>

        - <details>
          <summary><strong>Contesto</strong></summary>

          Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su macro simboliche e sostituzione testuale prima della compilazione. Si collega al blocco superiore Sintassi dichiarazione variabili > Il preprocessore. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
          </details>
        - <details>
          <summary><strong>Prerequisiti</strong></summary>

          Prima di affrontare "La direttiva #define" lo studente dovrebbe aver seguito il lavoro precedente su "Il preprocessore", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
          </details>
        - <details>
          <summary><strong>Obiettivi</strong></summary>

          Alla fine della lezione lo studente deve saper spiegare il ruolo di "La direttiva #define", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
          </details>
        - <details>
          <summary><strong>Richiamo</strong></summary>

          Richiama il passaggio precedente su "Il preprocessore" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
          </details>
        - <details>
          <summary><strong>Anticipazione</strong></summary>

          Questo argomento prepara il lavoro successivo su "La direttiva #include". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
          </details>
        - <details>
          <summary><strong>Prossimo passo</strong></summary>

          Dopo la spiegazione, proponi un esempio minimo su "La direttiva #define", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "La direttiva #include" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
          </details>
        - <details>
          <summary><strong>Rimando</strong></summary>

          Riferimento principale: README.md sezione "La direttiva #define" (../README.md#la-direttiva-define). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
          </details>
        </details>
      </details>
    - <details>
      <summary><a href="../README.md#la-direttiva-include">La direttiva #include</a> <code>README.md</code> H4 <code>draft</code></summary>

      - <details>
        <summary><strong>Cornice didattica</strong></summary>

        - <details>
          <summary><strong>Contesto</strong></summary>

          Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su inclusione di dichiarazioni e separazione tra interfaccia e implementazione. Si collega al blocco superiore Sintassi dichiarazione variabili > Il preprocessore. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
          </details>
        - <details>
          <summary><strong>Prerequisiti</strong></summary>

          Prima di affrontare "La direttiva #include" lo studente dovrebbe aver seguito il lavoro precedente su "La direttiva #define", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
          </details>
        - <details>
          <summary><strong>Obiettivi</strong></summary>

          Alla fine della lezione lo studente deve saper spiegare il ruolo di "La direttiva #include", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
          </details>
        - <details>
          <summary><strong>Richiamo</strong></summary>

          Richiama il passaggio precedente su "La direttiva #define" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
          </details>
        - <details>
          <summary><strong>Anticipazione</strong></summary>

          Questo argomento prepara il lavoro successivo su "Le direttive #if #ifdef #ifndef". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
          </details>
        - <details>
          <summary><strong>Prossimo passo</strong></summary>

          Dopo la spiegazione, proponi un esempio minimo su "La direttiva #include", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Le direttive #if #ifdef #ifndef" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
          </details>
        - <details>
          <summary><strong>Rimando</strong></summary>

          Riferimento principale: README.md sezione "La direttiva #include" (../README.md#la-direttiva-include). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
          </details>
        </details>
      </details>
    - <details>
      <summary><a href="../README.md#le-direttive-if-ifdef-ifndef">Le direttive #if #ifdef #ifndef</a> <code>README.md</code> H4 <code>draft</code></summary>

      - <details>
        <summary><strong>Cornice didattica</strong></summary>

        - <details>
          <summary><strong>Contesto</strong></summary>

          Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Sintassi dichiarazione variabili > Il preprocessore. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
          </details>
        - <details>
          <summary><strong>Prerequisiti</strong></summary>

          Prima di affrontare "Le direttive #if #ifdef #ifndef" lo studente dovrebbe aver seguito il lavoro precedente su "La direttiva #include", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
          </details>
        - <details>
          <summary><strong>Obiettivi</strong></summary>

          Alla fine della lezione lo studente deve saper spiegare il ruolo di "Le direttive #if #ifdef #ifndef", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
          </details>
        - <details>
          <summary><strong>Richiamo</strong></summary>

          Richiama il passaggio precedente su "La direttiva #include" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
          </details>
        - <details>
          <summary><strong>Anticipazione</strong></summary>

          Questo argomento prepara il lavoro successivo su "Eliminazione temporanea di codice". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
          </details>
        - <details>
          <summary><strong>Prossimo passo</strong></summary>

          Dopo la spiegazione, proponi un esempio minimo su "Le direttive #if #ifdef #ifndef", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Eliminazione temporanea di codice" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
          </details>
        - <details>
          <summary><strong>Rimando</strong></summary>

          Riferimento principale: README.md sezione "Le direttive #if #ifdef #ifndef" (../README.md#le-direttive-if-ifdef-ifndef). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
          </details>
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#eliminazione-temporanea-di-codice">Eliminazione temporanea di codice</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Sintassi dichiarazione variabili. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Eliminazione temporanea di codice" lo studente dovrebbe aver seguito il lavoro precedente su "Le direttive #if #ifdef #ifndef", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Eliminazione temporanea di codice", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Le direttive #if #ifdef #ifndef" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Protezione del contenuto dei file d'intestazione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Eliminazione temporanea di codice", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Protezione del contenuto dei file d'intestazione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Eliminazione temporanea di codice" (../README.md#eliminazione-temporanea-di-codice). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  - <details>
    <summary><a href="../README.md#protezione-del-contenuto-dei-file-dintestazione">Protezione del contenuto dei file d'intestazione</a> <code>README.md</code> H3 <code>draft</code></summary>

    - <details>
      <summary><strong>Cornice didattica</strong></summary>

      - <details>
        <summary><strong>Contesto</strong></summary>

        Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su apertura, lettura, scrittura e chiusura dei file tramite libreria standard C. Si collega al blocco superiore Sintassi dichiarazione variabili. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
        </details>
      - <details>
        <summary><strong>Prerequisiti</strong></summary>

        Prima di affrontare "Protezione del contenuto dei file d'intestazione" lo studente dovrebbe aver seguito il lavoro precedente su "Eliminazione temporanea di codice", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
        </details>
      - <details>
        <summary><strong>Obiettivi</strong></summary>

        Alla fine della lezione lo studente deve saper spiegare il ruolo di "Protezione del contenuto dei file d'intestazione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
        </details>
      - <details>
        <summary><strong>Richiamo</strong></summary>

        Richiama il passaggio precedente su "Eliminazione temporanea di codice" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
        </details>
      - <details>
        <summary><strong>Anticipazione</strong></summary>

        Questo argomento prepara il lavoro successivo su "Semplici operazioni di I/O sui file". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
        </details>
      - <details>
        <summary><strong>Prossimo passo</strong></summary>

        Dopo la spiegazione, proponi un esempio minimo su "Protezione del contenuto dei file d'intestazione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Semplici operazioni di I/O sui file" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
        </details>
      - <details>
        <summary><strong>Rimando</strong></summary>

        Riferimento principale: README.md sezione "Protezione del contenuto dei file d'intestazione" (../README.md#protezione-del-contenuto-dei-file-dintestazione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
        </details>
      </details>
    </details>
  </details>

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-9 - File, Makefile, debugging e progetto

<details>
<summary><strong>Apri contenuto UDA - Intermedio - 5 settimane</strong></summary>

- Percorso: `Intermedio`
- Settimane: `5`

#### Argomenti

- <details>
  <summary><a href="../README.md#semplici-operazioni-di-io-sui-file">Semplici operazioni di I/O sui file</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su apertura, lettura, scrittura e chiusura dei file tramite libreria standard C. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Semplici operazioni di I/O sui file" lo studente dovrebbe aver seguito il lavoro precedente su "Protezione del contenuto dei file d'intestazione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Semplici operazioni di I/O sui file", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Protezione del contenuto dei file d'intestazione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Creare ed Aprire i File". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Semplici operazioni di I/O sui file", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Creare ed Aprire i File" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Semplici operazioni di I/O sui file" (../README.md#semplici-operazioni-di-io-sui-file). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#creare-ed-aprire-i-file">Creare ed Aprire i File</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su apertura, lettura, scrittura e chiusura dei file tramite libreria standard C. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Creare ed Aprire i File" lo studente dovrebbe aver seguito il lavoro precedente su "Semplici operazioni di I/O sui file", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Creare ed Aprire i File", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Semplici operazioni di I/O sui file" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Leggere testo dai file con fgets()". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Creare ed Aprire i File", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Leggere testo dai file con fgets()" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Creare ed Aprire i File" (../README.md#creare-ed-aprire-i-file). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#leggere-testo-dai-file-con-fgets">Leggere testo dai file con fgets()</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su apertura, lettura, scrittura e chiusura dei file tramite libreria standard C. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Leggere testo dai file con fgets()" lo studente dovrebbe aver seguito il lavoro precedente su "Creare ed Aprire i File", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Leggere testo dai file con fgets()", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Creare ed Aprire i File" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Scrivere testo su file con fprintf()". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Leggere testo dai file con fgets()", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Scrivere testo su file con fprintf()" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Leggere testo dai file con fgets()" (../README.md#leggere-testo-dai-file-con-fgets). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#scrivere-testo-su-file-con-fprintf">Scrivere testo su file con fprintf()</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su apertura, lettura, scrittura e chiusura dei file tramite libreria standard C. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Scrivere testo su file con fprintf()" lo studente dovrebbe aver seguito il lavoro precedente su "Leggere testo dai file con fgets()", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Scrivere testo su file con fprintf()", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Leggere testo dai file con fgets()" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Dati in con fgets() e scanf()". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Scrivere testo su file con fprintf()", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Dati in con fgets() e scanf()" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Scrivere testo su file con fprintf()" (../README.md#scrivere-testo-su-file-con-fprintf). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#dati-in-con-fgets-e-scanf">Dati in con fgets() e scanf()</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su lettura dell'input, conversione dei dati e gestione dei casi problematici. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Dati in con fgets() e scanf()" lo studente dovrebbe aver seguito il lavoro precedente su "Scrivere testo su file con fprintf()", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Dati in con fgets() e scanf()", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Scrivere testo su file con fprintf()" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Utilizzando scanf() per l'inserimento di valori numerici". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Dati in con fgets() e scanf()", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Utilizzando scanf() per l'inserimento di valori numerici" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Dati in con fgets() e scanf()" (../README.md#dati-in-con-fgets-e-scanf). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#utilizzando-scanf-per-linserimento-di-valori-numerici">Utilizzando scanf() per l'inserimento di valori numerici</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su lettura dell'input, conversione dei dati e gestione dei casi problematici. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Utilizzando scanf() per l'inserimento di valori numerici" lo studente dovrebbe aver seguito il lavoro precedente su "Dati in con fgets() e scanf()", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Utilizzando scanf() per l'inserimento di valori numerici", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Dati in con fgets() e scanf()" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Convertire le stringhe in numeri con sscanf()". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Utilizzando scanf() per l'inserimento di valori numerici", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Convertire le stringhe in numeri con sscanf()" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Utilizzando scanf() per l'inserimento di valori numerici" (../README.md#utilizzando-scanf-per-linserimento-di-valori-numerici). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#convertire-le-stringhe-in-numeri-con-sscanf">Convertire le stringhe in numeri con sscanf()</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su array di char terminati da carattere nullo e funzioni di libreria associate. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Convertire le stringhe in numeri con sscanf()" lo studente dovrebbe aver seguito il lavoro precedente su "Utilizzando scanf() per l'inserimento di valori numerici", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Convertire le stringhe in numeri con sscanf()", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Utilizzando scanf() per l'inserimento di valori numerici" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Testo formattato con printf()". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Convertire le stringhe in numeri con sscanf()", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Testo formattato con printf()" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Convertire le stringhe in numeri con sscanf()" (../README.md#convertire-le-stringhe-in-numeri-con-sscanf). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#testo-formattato-con-printf">Testo formattato con printf()</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su formattazione dell'output e corrispondenza tra specificatori e argomenti. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Testo formattato con printf()" lo studente dovrebbe aver seguito il lavoro precedente su "Convertire le stringhe in numeri con sscanf()", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Testo formattato con printf()", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Convertire le stringhe in numeri con sscanf()" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Passaggio di parametri a printf()". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Testo formattato con printf()", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Passaggio di parametri a printf()" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Testo formattato con printf()" (../README.md#testo-formattato-con-printf). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#passaggio-di-parametri-a-printf">Passaggio di parametri a printf()</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su formattazione dell'output e corrispondenza tra specificatori e argomenti. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Passaggio di parametri a printf()" lo studente dovrebbe aver seguito il lavoro precedente su "Testo formattato con printf()", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Passaggio di parametri a printf()", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Testo formattato con printf()" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Linking alla libreria standard del C". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Passaggio di parametri a printf()", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Linking alla libreria standard del C" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Passaggio di parametri a printf()" (../README.md#passaggio-di-parametri-a-printf). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#linking-alla-libreria-standard-del-c">Linking alla libreria standard del C</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Linking alla libreria standard del C" lo studente dovrebbe aver seguito il lavoro precedente su "Passaggio di parametri a printf()", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Linking alla libreria standard del C", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Passaggio di parametri a printf()" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Costruzione di librerie di procedure esterne". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Linking alla libreria standard del C", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Costruzione di librerie di procedure esterne" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Linking alla libreria standard del C" (../README.md#linking-alla-libreria-standard-del-c). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#costruzione-di-librerie-di-procedure-esterne">Costruzione di librerie di procedure esterne</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su organizzazione del codice in moduli riusabili e collegamento con il linker. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Costruzione di librerie di procedure esterne" lo studente dovrebbe aver seguito il lavoro precedente su "Linking alla libreria standard del C", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Costruzione di librerie di procedure esterne", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Linking alla libreria standard del C" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Collegare le librerie nei tuoi programmi". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Costruzione di librerie di procedure esterne", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Collegare le librerie nei tuoi programmi" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Costruzione di librerie di procedure esterne" (../README.md#costruzione-di-librerie-di-procedure-esterne). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#collegare-le-librerie-nei-tuoi-programmi">Collegare le librerie nei tuoi programmi</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su organizzazione del codice in moduli riusabili e collegamento con il linker. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Collegare le librerie nei tuoi programmi" lo studente dovrebbe aver seguito il lavoro precedente su "Costruzione di librerie di procedure esterne", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Collegare le librerie nei tuoi programmi", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Costruzione di librerie di procedure esterne" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Note sulla raccolta delle procedure in librerie". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Collegare le librerie nei tuoi programmi", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Note sulla raccolta delle procedure in librerie" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Collegare le librerie nei tuoi programmi" (../README.md#collegare-le-librerie-nei-tuoi-programmi). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#note-sulla-raccolta-delle-procedure-in-librerie">Note sulla raccolta delle procedure in librerie</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su organizzazione del codice in moduli riusabili e collegamento con il linker. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Note sulla raccolta delle procedure in librerie" lo studente dovrebbe aver seguito il lavoro precedente su "Collegare le librerie nei tuoi programmi", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Note sulla raccolta delle procedure in librerie", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Collegare le librerie nei tuoi programmi" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "Gcc --no-pie". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Note sulla raccolta delle procedure in librerie", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Gcc --no-pie" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Note sulla raccolta delle procedure in librerie" (../README.md#note-sulla-raccolta-delle-procedure-in-librerie). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>
- <details>
  <summary><a href="../README.md#gcc---no-pie">Gcc --no-pie</a> <code>README.md</code> H3 <code>draft</code></summary>

  - <details>
    <summary><strong>Cornice didattica</strong></summary>

    - <details>
      <summary><strong>Contesto</strong></summary>

      Questo argomento si colloca nell'UDA "File, Makefile, debugging e progetto" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
      </details>
    - <details>
      <summary><strong>Prerequisiti</strong></summary>

      Prima di affrontare "Gcc --no-pie" lo studente dovrebbe aver seguito il lavoro precedente su "Note sulla raccolta delle procedure in librerie", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
      </details>
    - <details>
      <summary><strong>Obiettivi</strong></summary>

      Alla fine della lezione lo studente deve saper spiegare il ruolo di "Gcc --no-pie", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
      </details>
    - <details>
      <summary><strong>Richiamo</strong></summary>

      Richiama il passaggio precedente su "Note sulla raccolta delle procedure in librerie" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
      </details>
    - <details>
      <summary><strong>Anticipazione</strong></summary>

      Questo argomento prepara il lavoro successivo su "il consolidamento attraverso esercizi, debug e progetto". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
      </details>
    - <details>
      <summary><strong>Prossimo passo</strong></summary>

      Dopo la spiegazione, proponi un esempio minimo su "Gcc --no-pie", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "il consolidamento attraverso esercizi, debug e progetto" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
      </details>
    - <details>
      <summary><strong>Rimando</strong></summary>

      Riferimento principale: README.md sezione "Gcc --no-pie" (../README.md#gcc---no-pie). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
      </details>
    </details>
  </details>

</details>
</td>
</tr>
</table>

## Quarto anno

Linux programming, processi e thread

- Ore settimanali: `3`
- Settimane: `33`

<table align="center">
<thead>
<tr>
<th align="center">UDA</th>
<th align="center">Percorso</th>
<th align="center">Settimane</th>
<th align="center">Argomenti</th>
</tr>
</thead>
<tbody>
<tr>
<td align="center"><div align="justify"><code>uda-10</code> Ripartenza C/Linux, API e qualita</div></td>
<td align="center"><div align="justify">Avanzato</div></td>
<td align="center"><div align="justify">1-5</div></td>
<td align="center"><div align="justify">0</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-11</code> Processi</div></td>
<td align="center"><div align="justify">Avanzato</div></td>
<td align="center"><div align="justify">6-12</div></td>
<td align="center"><div align="justify">0</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-12</code> Segnali e progetto processi</div></td>
<td align="center"><div align="justify">Avanzato</div></td>
<td align="center"><div align="justify">13-15</div></td>
<td align="center"><div align="justify">0</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-13</code> Thread</div></td>
<td align="center"><div align="justify">Avanzato</div></td>
<td align="center"><div align="justify">16-20</div></td>
<td align="center"><div align="justify">0</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-14</code> Sincronizzazione</div></td>
<td align="center"><div align="justify">Avanzato</div></td>
<td align="center"><div align="justify">21-25</div></td>
<td align="center"><div align="justify">0</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-15</code> I/O, processi e socket intro</div></td>
<td align="center"><div align="justify">Avanzato</div></td>
<td align="center"><div align="justify">26-28</div></td>
<td align="center"><div align="justify">0</div></td>
</tr>
<tr>
<td align="center"><div align="justify"><code>uda-16</code> Sicurezza, CI, manutenzione e progetto finale</div></td>
<td align="center"><div align="justify">Avanzato</div></td>
<td align="center"><div align="justify">29-33</div></td>
<td align="center"><div align="justify">0</div></td>
</tr>
</tbody>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-10 - Ripartenza C/Linux, API e qualita

<details>
<summary><strong>Apri contenuto UDA - Avanzato - 1-5 settimane</strong></summary>

- Percorso: `Avanzato`
- Settimane: `1-5`

#### Argomenti

- Da progettare nella Course Design Board.

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-11 - Processi

<details>
<summary><strong>Apri contenuto UDA - Avanzato - 6-12 settimane</strong></summary>

- Percorso: `Avanzato`
- Settimane: `6-12`

#### Argomenti

- Da progettare nella Course Design Board.

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-12 - Segnali e progetto processi

<details>
<summary><strong>Apri contenuto UDA - Avanzato - 13-15 settimane</strong></summary>

- Percorso: `Avanzato`
- Settimane: `13-15`

#### Argomenti

- Da progettare nella Course Design Board.

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-13 - Thread

<details>
<summary><strong>Apri contenuto UDA - Avanzato - 16-20 settimane</strong></summary>

- Percorso: `Avanzato`
- Settimane: `16-20`

#### Argomenti

- Da progettare nella Course Design Board.

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-14 - Sincronizzazione

<details>
<summary><strong>Apri contenuto UDA - Avanzato - 21-25 settimane</strong></summary>

- Percorso: `Avanzato`
- Settimane: `21-25`

#### Argomenti

- Da progettare nella Course Design Board.

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-15 - I/O, processi e socket intro

<details>
<summary><strong>Apri contenuto UDA - Avanzato - 26-28 settimane</strong></summary>

- Percorso: `Avanzato`
- Settimane: `26-28`

#### Argomenti

- Da progettare nella Course Design Board.

</details>
</td>
</tr>
</table>

<table align="center">
<tr>
<td width="900">

### UDA-16 - Sicurezza, CI, manutenzione e progetto finale

<details>
<summary><strong>Apri contenuto UDA - Avanzato - 29-33 settimane</strong></summary>

- Percorso: `Avanzato`
- Settimane: `29-33`

#### Argomenti

- Da progettare nella Course Design Board.

</details>
</td>
</tr>
</table>

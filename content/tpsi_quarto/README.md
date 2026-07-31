# TPSI quarto anno — indice delle risorse

Questa cartella contiene materiali didattici originali per il quarto anno TPSI, organizzati come fonte locale importabile dalla Course Board di 2cornot2c.

## Moduli

1. [Processi, thread e concorrenza](01_PROCESSI_E_CONCORRENZA.md)
2. [Comunicazione e sincronizzazione](02_COMUNICAZIONE_E_SINCRONIZZAZIONE.md)
3. [Requisiti software](03_REQUISITI_SOFTWARE.md)
4. [Documentazione e controllo di versione](04_DOCUMENTAZIONE_VERSIONAMENTO.md)
5. [Testing e debugging](05_TESTING_DEBUGGING.md)
6. [Cittadinanza digitale](06_CITTADINANZA_DIGITALE.md)

## File di controllo

- [`manifest.json`](manifest.json): identità, fonti, versioni e relazioni del pacchetto;
- [`COVERAGE.md`](COVERAGE.md): corrispondenza tra indice curricolare, moduli, sezioni Linux e activity;
- [`doc/TPSI_QUARTO_CONTENT_PACK.md`](../../doc/TPSI_QUARTO_CONTENT_PACK.md): contratto operativo e regole di integrazione.

## Provenienza e diritto d'autore

Il riferimento curricolare è l'indice pubblico del volume 2 Hoepli *Tecnologie e progettazione di sistemi informatici e di telecomunicazioni*, di Paolo Camagni e Riccardo Nikolassy.

I testi, gli esempi, gli esercizi e i laboratori presenti in questa cartella sono nuovi e non costituiscono una trascrizione del volume. Il riferimento al libro serve a verificare la copertura degli argomenti. Eventuali risorse ufficiali dell'editore devono essere gestite separatamente nel rispetto delle rispettive licenze.

## Relazione con `LINUX_PROGRAMMING.md`

Il pacchetto usa `LINUX_PROGRAMMING.md` come seconda fonte locale. Sono pertinenti le sezioni a partire da:

```text
## Linux Programming
```

La sezione precedente:

```text
## Controllo dei processi
```

è esclusa dal percorso perché il docente ha richiesto di non integrarla.

I moduli non duplicano l'intera dispensa Linux: introducono la cornice concettuale, collegano gli heading pertinenti e aggiungono contenuti mancanti, confronti Java, esercizi, laboratori e verifiche.

## Uso nella Course Board

1. Avvia il server locale:

   ```bash
   python scripts/course_board_server.py
   ```

2. Apri `tools/course_board.html`.
3. Carica il progetto archiviato `tpsi_quarto_2026_2027.json`.
4. Esplora le fonti `TPSI quarto — contenuti originali` e `Linux Programming`.
5. Trascina gli heading nelle UDA, oppure modifica gli item già proposti.
6. Collega le activity dalla dashboard docente.

## Stati di revisione

I contenuti usano i seguenti stati:

- `draft`: bozza non ancora verificata dal docente;
- `reviewed`: controllata dal punto di vista tecnico o didattico;
- `approved`: pronta per la pubblicazione agli studenti;
- `superseded`: sostituita da una versione successiva;
- `retired`: non più usata nei nuovi percorsi.

Il primo rilascio del pacchetto resta `draft` finché non sono completati il controllo docente, la validazione delle activity e il collaudo dalla dashboard.
# Note docente — quadrato con `fork` e pipe

## Collocazione

- percorso: `quarto-anno`;
- UDA principale: `uda-11`;
- ripresa in `uda-12` e `uda-15`;
- contenuti: processi, IPC, gestione degli errori, test deterministici.

## Obiettivi osservabili

Lo studente deve saper spiegare:

1. quali descrittori possiede ciascun processo dopo `fork`;
2. perché le estremità non usate devono essere chiuse;
3. perché il padre usa `waitpid`;
4. quale dato attraversa la pipe;
5. perché stdout deve rispettare un contratto deterministico.

## Errori attesi

- padre e figlio eseguono lo stesso ramo;
- risultato calcolato dal padre;
- descrittori non chiusi;
- `waitpid` assente;
- una sola `read`/`write` senza ragionare sul contratto;
- diagnostica su stdout;
- input non validato;
- stato del figlio ignorato.

## Estensioni

- inviare una struttura richiesta/risposta;
- usare due pipe per un protocollo bidirezionale;
- aggiungere controllo overflow prima del quadrato;
- sostituire il calcolo con un programma avviato tramite `exec`;
- confrontare il protocollo con una `BlockingQueue` Java.

## Valutazione

I test automatici coprono il contratto di I/O. La rubrica docente verifica l'uso reale delle primitive, la gestione delle risorse e la spiegazione del protocollo. Un programma che stampa gli output corretti senza usare la pipe non soddisfa la consegna e non può ottenere il punteggio pieno.

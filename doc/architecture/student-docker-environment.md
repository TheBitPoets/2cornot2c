# Ambiente Docker leggero per gli studenti

## Shell student-dev ed editor

Il launcher Windows usa `scripts/student_dev_shell.py` e il lock dedicato
`docker/student-dev/toolchain.lock.json`. Il comando descritto nella prima
iterazione sotto rimane la shell del grading, distinta da student-dev.

La build student-dev 2026.09.1 aggiunge `micro=2.0.13-1`, fissato nel manifest
`docker/student-dev/toolchain.json` e installato dallo snapshot Ubuntu esistente.
Imposta `EDITOR=micro` e `VISUAL=micro`, conservando Vim. La versione del
[pacchetto Noble](https://packages.ubuntu.com/noble/amd64/editors/micro) e
disponibile anche per ARM64. Nessuna variazione alla toolchain del grading.

Il launcher monta gia `/home/student` su tmpfs scrivibile per configurazione e
stato degli editor; il workspace montato dall'host conserva i sorgenti. Questi
mount restano necessari con filesystem radice read-only. La configurazione
dell'editor nel tmpfs non persiste tra contenitori.

Il lock 2026.07.1 identifica ancora la vecchia immagine senza micro. Il manifest
di build 2026.09.1 descrive la nuova: non attribuire i suoi risultati al digest
precedente. Prima della distribuzione occorrono build e smoke AMD64/ARM64,
pubblicazione con nuovo digest, aggiornamento del lock e rigenerazione del
candidato Windows con manifest/hash, poi collaudo dal launcher installato.
Non sovrascrivere un digest o i manifest del candidato gia qualificato.

## Prima iterazione

La prima soluzione Docker non introduce subito una seconda immagine. Avvia una
shell usando l'esatto riferimento immutabile del runner di grading:

```bash
python -m scripts.student_docker_shell --workspace lab
```

Questo garantisce subito le stesse versioni di GCC, Python, Node.js e SQLite
usate per correggere gli esercizi. Il workspace scelto è l'unica directory
scrivibile persistente.

Il container:

- usa 512 MB di RAM e una CPU;
- gira come utente non root;
- non ha rete;
- elimina tutte le capability Linux;
- usa root filesystem in sola lettura;
- limita processi e privilegi;
- viene eliminato all'uscita.

È possibile vedere il comando senza eseguirlo:

```bash
python -m scripts.student_docker_shell --workspace lab --print-command
```

## Limiti intenzionali

Il runner corrente è pubblicato soltanto per `linux/amd64`. Su Windows amd64
Docker lo esegue nativamente; su Apple Silicon richiede emulazione e non è
ancora il percorso raccomandato per poca RAM.

La shell contiene la toolchain del grading ma non ancora editor, Make e GDB.
La seconda iterazione produrrà un'immagine `student-dev` multiarch derivata
dallo stesso manifest riproducibile, aggiungendo soltanto gli strumenti
interattivi. Il runner autorevole resterà separato e più piccolo.

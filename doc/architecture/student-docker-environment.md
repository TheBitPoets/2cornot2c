# Ambiente Docker leggero per gli studenti

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

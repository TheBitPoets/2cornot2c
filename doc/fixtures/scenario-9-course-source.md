# Fonte di collaudo per il percorso docente

Questa fixture contiene paragrafi e riferimenti immagine controllati per lo Scenario 9. Non sostituirla con contenuti didattici reali durante il collaudo.

## Paragrafo da aggiungere alla UDA

Testo completo del paragrafo usato per verificare catalogo, inserimento, deduplicazione e modal `Testo`.

## Immagine locale valida

L'immagine seguente deve essere servita dalla stessa root della fonte e restare confinata nel modal.

![Panoramica locale del percorso docente](../images/dashboard-guides/scenario-9-docente-percorso-colori.png)

## Immagine locale mancante

Il contenuto deve restare leggibile e mostrare il fallback testuale.

![Fixture locale mancante](../images/dashboard-guides/scenario-9-missing.png)

## Immagine fuori dalla root

Il riferimento seguente deve essere respinto senza leggere file esterni alla root configurata.

![Fixture fuori dalla root](../../../scenario-9-outside.png)

## Immagine con URL esterno

Il riferimento seguente deve essere respinto senza richieste di rete.

![Fixture esterna](https://example.invalid/scenario-9.png)

## Immagine con estensione non grafica

Il riferimento seguente deve essere respinto prima di tentare la lettura.

![Fixture non grafica](../images/dashboard-guides/scenario-9-not-image.txt)

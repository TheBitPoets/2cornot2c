## Cornice didattica

<table align="center">
<tr>
<td>
<details>
<summary>&#128506; Cornice didattica</summary>

<p align="justify">
<strong>&#128506; Contesto:</strong>
Qui spiega in due o tre frasi da quale punto del percorso arriva lo studente. Il testo deve aiutare la lettura sequenziale: "finora abbiamo visto...", "adesso facciamo un passo in piu...", "questo argomento serve per...".
</p>

<p align="justify">
<strong>&#128736; Prerequisiti:</strong>
<a href="#sezione-precedente">Nome sezione precedente</a>,
<a href="#altra-sezione">Nome altra sezione</a>.
</p>

<p align="justify">
<strong>&#127919; Obiettivi:</strong>
Alla fine di questa sezione saprai descrivere il concetto principale, riconoscere gli errori piu comuni e applicare il meccanismo in un piccolo programma.
</p>

<p align="justify">
<strong>&#10145; Prossimo passo:</strong>
Qui spiega dove porta naturalmente la sezione successiva. Il testo deve mantenere il filo narrativo per chi legge la dispensa dall'inizio alla fine.
</p>
</details>
</td>
</tr>
</table>

## Richiamo

<table align="center">
<tr>
<td>
<p align="justify">
<strong>&#128257; Richiamo:</strong>
Questo concetto e stato introdotto nella sezione <a href="#sezione-gia-vista">Nome sezione gia vista</a>. Qui lo riprendiamo solo per usarlo nel nuovo contesto.
</p>
</td>
</tr>
</table>

## Anticipazione

<table align="center">
<tr>
<td>
<p align="justify">
<strong>&#128064; Anticipazione:</strong>
Qui compare il concetto di <code>concetto futuro</code>. Per ora ti basta sapere che ... Lo studieremo in dettaglio nella sezione <a href="#sezione-futura">Nome sezione futura</a>.
</p>
</td>
</tr>
</table>

## Rimando

<table align="center">
<tr>
<td>
<p align="justify">
<strong>&#128279; Rimando:</strong>
Questo dettaglio sara ripreso piu avanti nella sezione <a href="#sezione-futura">Nome sezione futura</a>. Per ora puoi ignorarlo senza perdere il filo principale.
</p>
</td>
</tr>
</table>

## Lab

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/0_intro/0_hello.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Primo programma C: stampa un messaggio a schermo e introduce la struttura minima di un programma.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Questo laboratorio mostra come includere un header standard, definire la funzione <code>main()</code>, chiamare <code>printf()</code>, compilare il sorgente con <code>gcc</code> ed eseguire il binario prodotto. È il punto di partenza per collegare codice sorgente, compilazione ed esecuzione.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/0_hello.c">
          /lab/0_intro/0_hello.c
        </a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/0_intro
gcc -o bin/0_hello 0_hello.c
bin/0_hello</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/0_intro/0_hello.c" -->
<pre lang="c"><code>/*
 * 0_intro -- Primo esempio di programma in c
 *
 * Cosa imparerai:
 *	*) Cosa sono gli header files
 *      *) Concetto di funzione e chiamata di funzione
 *	*) Processo di creazione di un file eseguibile (binario)
 *
 * Utilizzo:
 *      gcc -o bin/0_hello 0_hello.c
 *      bin/0_hello	      
 */

#include &lt;stdio.h&gt;

int main(void){
	printf("Hello World\n");
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/0_intro/output/0_hello.txt" -->
<pre lang="text"><code>Hello World
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

## Lab

<details>
<summary>/lab/0_intro/0_hello.c</summary>
<a href="https://github.com/kinderp/2cornot2c/blob/18b60e866c1e0e22c59835fe953cbe3c534e7422/lab/0_intro/0_hello.c">/lab/0_intro/0_hello.c</a>
	<ul>
		<li>Entra nella macchina Linux con vagrant ssh</li>
		<li>Spostati nella cartella lab/0_intro</li>
		<li>Compila il file 0_hello.c. L'eseguibile finale deve avere nome bin/0_hello</li>
	</ul>
</details>


## Importante

<table align="center">
	<td>&#10071; <b>Importante</b>
	<p align=justify>
 Una <b>variabile</b> è una locazione di memoria a cui è stato associato un <b>identificatore</b>, cioè un nome per referenziare nel codice quella cella di memoria.
	</p>
	</td>
</table>

## Attenzione

<table align="center">
	<td>&#9888; <b>Attenzione</b>
	<p align=justify>
Le variabili possono essere sia dichiarate che definite e spesso i due termini sono usati per esprimere la stessa cosa. è prematuro spiegarne la lieve differenza, ma tieni a mente per adesso che i due termini non sono la stessa cosa.
	</p>
	</td>
</table>

## Nota

<table align="center">
	<td>:pill: <b>Nota</b>
	<p align=justify>
 Storicamente le variabili con <b>block scope</b> dovevano essere dichiarate all'inizio del blocco.
	</p>
	<p align=justify>
Dal C99 è possibile dichiarare le variabili all'interno del blocco in qualsiasi posizione al suo interno.
Questo è utile soprattutto per le variabili indice di un ciclo o per documentare meglio il proprio codice, dichiarando le variabili il più vicino possibile alla riga che ne fa effettivamente uso.
	</p>
	</td>
</table>

## Lab

<details>
<summary>&#128187; <code>/lab/0_intro/0_hello.c</code></summary>

<table align="center">
  <tr>
    <td>
      <p align="justify">
        <strong>Descrizione breve:</strong>
        Primo programma C: stampa un messaggio a schermo e introduce la struttura minima di un programma.
      </p>

      <p align="justify">
        <strong>Descrizione lunga:</strong>
        Questo laboratorio mostra come includere un header standard, definire la funzione <code>main()</code>,
        chiamare <code>printf()</code>, compilare il sorgente con <code>gcc</code> ed eseguire il binario prodotto.
        È il punto di partenza per collegare codice sorgente, compilazione ed esecuzione.
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
    </td>
  </tr>
</table>

</details>

## Lab

<details>
<summary>/lab/0_intro/0_hello.c</summary>
<a href="https://github.com/kinderp/2cornot2c/blob/18b60e866c1e0e22c59835fe953cbe3c534e7422/lab/0_intro/0_hello.c">/lab/0_intro/0_hello.c</a>
	<ul>
		<li>Entra nella macchina Linux con <code>vagrant ssh</code></li>
		<li>Spostati nella cartella <code>lab/0_intro</code></li>
		<li>Compila il file <code>0_hello.c</code>. L'eseguibile finale deve avere nome <code>bin/0_hello</code></li>
	</ul>
</details>


## Importante

<table align="center">
	<td>:exclamation: <b>Importante</b>
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
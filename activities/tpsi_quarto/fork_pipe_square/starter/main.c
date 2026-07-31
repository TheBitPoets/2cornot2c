#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void) {
    long value = 0;

    if (scanf("%ld", &value) != 1) {
        puts("Input non valido");
        return EXIT_FAILURE;
    }

    /*
     * TODO:
     * 1. crea una pipe;
     * 2. crea il figlio con fork();
     * 3. nel figlio calcola il quadrato e invialo nella pipe;
     * 4. nel padre leggi il risultato, attendi il figlio e stampalo.
     *
     * Lo starter restituisce intenzionalmente il valore senza usare processi:
     * compila, ma non soddisfa la consegna.
     */
    printf("Risultato: %ld\n", value);
    return EXIT_SUCCESS;
}

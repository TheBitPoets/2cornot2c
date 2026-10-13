#include <stdio.h>
#include <string.h>

int main(void) {
    char ciao[] = "ciao";

    /* L'array non e' assegnabile, ma i suoi elementi sono modificabili. */
    // ciao = "miao";  /* Errore: un array non e' assegnabile. */
    ciao[0] = 'm';
    printf("%s\n", ciao);     // (1) miao

    /* Qui strcpy e' valida: ciao contiene cinque char, compreso '\0'. */
    strcpy(ciao, "ciao");
    printf("%s\n", ciao);     // (2) ciao

    printf("\n");

    /* Il puntatore e' riassegnabile, ma i literal non vanno modificati. */
    const char *ciao_ = "ciao";
    printf("%s\n", ciao_);    // (3) ciao

    ciao_ = "miao";
    printf("%s\n", ciao_);    // (4) miao

    return 0;
}

#include <stdio.h>
#include "text_utils.h"

int main(void) {
    char line[] = "ciao mondo";
    printf("%d %d\n", count_words(line), count_letters(line));
    return 0;
}

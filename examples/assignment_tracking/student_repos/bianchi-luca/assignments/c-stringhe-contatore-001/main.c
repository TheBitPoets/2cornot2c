#include <stdio.h>

#include "text_utils.h"

int main(void) {
    char line[256] = "one two  three";
    printf("words=%d\n", count_words(line));
    printf("letters=%d\n", count_letters(line));
    return 0;
}

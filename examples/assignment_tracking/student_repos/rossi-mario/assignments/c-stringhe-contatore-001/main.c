#include <stdio.h>

#include "text_utils.h"

int main(void) {
    char line[256] = "C is small, sharp, and close to memory.";
    int words = count_words(line);
    int letters = count_letters(line);

    printf("words=%d letters=%d\n", words, letters);
    return 0;
}

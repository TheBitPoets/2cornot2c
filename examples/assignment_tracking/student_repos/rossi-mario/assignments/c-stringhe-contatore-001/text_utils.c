#include "text_utils.h"

#include <ctype.h>
#include <stdbool.h>

int count_words(const char *text) {
    int count = 0;
    bool inside_word = false;

    for (int i = 0; text[i] != '\0'; i++) {
        if (isspace((unsigned char)text[i])) {
            inside_word = false;
        } else if (!inside_word) {
            count++;
            inside_word = true;
        }
    }

    return count;
}

int count_letters(const char *text) {
    int count = 0;

    for (int i = 0; text[i] != '\0'; i++) {
        if (isalpha((unsigned char)text[i])) {
            count++;
        }
    }

    return count;
}

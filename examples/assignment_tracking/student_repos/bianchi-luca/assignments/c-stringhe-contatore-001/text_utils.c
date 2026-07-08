#include "text_utils.h"

int count_words(const char *text) {
    int count = 1;

    for (int i = 0; text[i] != '\0'; i++) {
        if (text[i] == ' ') {
            count++;
        }
    }

    return count;
}

int count_letters(const char *text) {
    int count = 0;

    for (int i = 0; text[i] != '\0'; i++) {
        if (text[i] != ' ') {
            count++;
        }
    }

    return count;
}

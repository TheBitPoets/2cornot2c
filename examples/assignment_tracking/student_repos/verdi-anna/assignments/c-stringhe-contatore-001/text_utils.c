#include "text_utils.h"

int count_words(const char *text) {
    int words = 0;
    int in_word = 0;
    for (int i = 0; text[i] != '\0'; i++) {
        if (text[i] == ' ' || text[i] == '\t' || text[i] == '\n') {
            in_word = 0;
        } else if (!in_word) {
            words++;
            in_word = 1;
        }
    }
    return words;
}

int count_letters(const char *text) {
    int letters = 0;
    for (int i = 0; text[i] != '\0'; i++) {
        if ((text[i] >= 'a' && text[i] <= 'z') || (text[i] >= 'A' && text[i] <= 'Z')) {
            letters++;
        }
    }
    return letters;
}

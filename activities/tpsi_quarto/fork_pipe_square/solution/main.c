#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static int write_exact(int fd, const void *buffer, size_t size) {
    const unsigned char *cursor = buffer;
    size_t written = 0;

    while (written < size) {
        ssize_t count = write(fd, cursor + written, size - written);
        if (count < 0) {
            if (errno == EINTR) {
                continue;
            }
            return -1;
        }
        written += (size_t)count;
    }

    return 0;
}

static int read_exact(int fd, void *buffer, size_t size) {
    unsigned char *cursor = buffer;
    size_t received = 0;

    while (received < size) {
        ssize_t count = read(fd, cursor + received, size - received);
        if (count == 0) {
            return -1;
        }
        if (count < 0) {
            if (errno == EINTR) {
                continue;
            }
            return -1;
        }
        received += (size_t)count;
    }

    return 0;
}

int main(void) {
    long value = 0;

    if (scanf("%ld", &value) != 1) {
        puts("Input non valido");
        return EXIT_FAILURE;
    }

    int channel[2];
    if (pipe(channel) < 0) {
        perror("pipe");
        return EXIT_FAILURE;
    }

    pid_t child = fork();
    if (child < 0) {
        perror("fork");
        close(channel[0]);
        close(channel[1]);
        return EXIT_FAILURE;
    }

    if (child == 0) {
        close(channel[0]);

        long result = value * value;
        int write_result = write_exact(channel[1], &result, sizeof result);
        close(channel[1]);

        return write_result == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
    }

    close(channel[1]);

    long result = 0;
    int read_result = read_exact(channel[0], &result, sizeof result);
    close(channel[0]);

    int status = 0;
    pid_t waited = waitpid(child, &status, 0);
    if (waited < 0) {
        perror("waitpid");
        return EXIT_FAILURE;
    }

    if (read_result < 0 || !WIFEXITED(status) || WEXITSTATUS(status) != 0) {
        fputs("Comunicazione con il figlio non riuscita\n", stderr);
        return EXIT_FAILURE;
    }

    printf("Risultato: %ld\n", result);
    return EXIT_SUCCESS;
}

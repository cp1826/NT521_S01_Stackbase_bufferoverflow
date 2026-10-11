#include <stdio.h>
#include <string.h>

/* Intentionally vulnerable teaching example. Run only in the lab VM. */
static void copy_input(const char *input)
{
    char buffer[8] = {0};

    printf("capacity=%zu, input_bytes=%zu, required_bytes=%zu\n",
           sizeof buffer, strlen(input), strlen(input) + 1);
    fflush(stdout); /* Preserve this line even if the next operation aborts. */

    /* BUG: strcpy copies the terminating NUL too, without a size check. */
    strcpy(buffer, input);

    printf("buffer=\"%s\"\n", buffer);
    puts("Copy returned. This alone does not prove memory safety.");
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <ASCII-string>\n", argv[0]);
        return 2;
    }
    copy_input(argv[1]);
    return 0;
}

#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdio.h>
#include <errno.h>

#include "io_helpers.h"


// ===== Output helpers =====

/* Prereq: str is a NULL terminated string
 */
void display_message(char *str) {
    write(STDOUT_FILENO, str, strnlen(str, MAX_STR_LEN));
}


/* Prereq: pre_str, str are NULL terminated string
 */
void display_error(char *pre_str, char *str) {
    write(STDERR_FILENO, pre_str, strnlen(pre_str, MAX_STR_LEN));
    write(STDERR_FILENO, str, strnlen(str, MAX_STR_LEN));
    write(STDERR_FILENO, "\n", 1);
}


// ===== Input tokenizing =====

/* Prereq: in_ptr points to a character buffer of size > MAX_STR_LEN
 * Return: number of bytes read
 */
ssize_t get_input(char *in_ptr) { 
    ssize_t i = 0;
    char c;

    while (1) {
        ssize_t r = read(STDIN_FILENO, &c, 1);

        if (r == 0) { 
            if (i == 0) {
                in_ptr[0] = '\0';
                return -2;
            }
            break; // treat partial data as a final line
        }

        if (r < 0) { // read error
            if (errno == EINTR){
                // interrupted by signal, SIGINT, not an error
                in_ptr[0] = '\0';
                return -1;
            }
            in_ptr[0] = '\0';
            return -1;
        }

        // If we already have 128 chars and next char isn't newline, line is too long
        if (i == MAX_STR_LEN && c != '\n') {
            write(STDERR_FILENO, "ERROR: input line too long\n",
                  strlen("ERROR: input line too long\n"));

            // flush rest of this line
            while (read(STDIN_FILENO, &c, 1) == 1 && c != '\n') { }

            in_ptr[0] = '\0';
            return -1;
        }

        if (c == '\n') {
            break;
        }

        in_ptr[i++] = c;
    }

    in_ptr[i] = '\0';
    return i;
}

/* Prereq: in_ptr is a string, tokens is of size >= len(in_ptr)
 * Warning: in_ptr is modified
 * Return: number of tokens.
 */
size_t tokenize_input(char *in_ptr, char **tokens) {
    // TODO: Remove unused attribute
    char *curr_ptr = strtok (in_ptr, DELIMITERS); // strtok splits in_ptr to multiple pieces (tokens) using delimeters (DELIMITERS)
    size_t token_count = 0; // DELIMTERS collapses whitespace

    while (curr_ptr != NULL) {  // TODO: Fix this
        size_t increment = token_count++;
        tokens[increment] = curr_ptr;
        curr_ptr = strtok(NULL, DELIMITERS);
    }
    tokens[token_count] = NULL;
    return token_count;
}

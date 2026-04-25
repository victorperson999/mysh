#ifndef __VARIABLES_H__
#define __VARIABLES_H__

#include <stddef.h>

typedef struct {
    char *name;
    char *value;
}var_t;

typedef struct {
    var_t *arr;
    size_t len;
    size_t cap;
} var_table_t;

void vars_init(var_table_t *t);
void vars_destroy(var_table_t *t);

const char *vars_get(const var_table_t *t, const char *name);
// return 0 on success -1 on OOM
int set_variable(var_table_t *t, const char *name, const char *value);

// expand $var in input, return malloced string or null on OOM
// make sure that max token length is 128 by truncating within the tokens
char *expand_line(const char *input, const var_table_t *t);


#endif
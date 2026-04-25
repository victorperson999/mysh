#include <stdlib.h>
#include <string.h>

#include "variables.h"
#include "io_helpers.h"

static char *xstrdup(const char *s){
    if (!s) s="";
    size_t n = strlen(s);
    char *p = malloc(n+1);
    if (!p) return NULL;
    memcpy(p, s, n+1);
    return p;
}

static int is_ws(char c){
    return (c == ' ' || c == '\t' || c == '\n');
}

static int ensure_cap(var_table_t *t, size_t need){
    if (t->cap >= need){
        return 0;
    }
    size_t new_cap = (t->cap == 0) ? 8: t->cap;
    while (new_cap < need){
        new_cap *= 2;
    }
    var_t *new_arr = realloc(t->arr, new_cap*sizeof(var_t));
    if (!new_arr){
        return -1;
    }
    t->arr = new_arr;
    t->cap = new_cap;
    return 0;
}

static int out_ensure(char **out, size_t *cap, size_t need){
    if (*cap >= need){
        return 0;
    }
    size_t new_cap = (*cap == 0) ? 256: *cap;
    while (new_cap < need){
        new_cap *= 2;
    }
    char *p = realloc(*out, new_cap);
    if (!p){
        return -1;
    }
    *out = p;
    *cap = new_cap;
    return 0;
}

static int out_append_char(char **out, size_t *len, size_t *cap, char c){
    if (out_ensure(out, cap, (*len)+2)==-1){
        return -1;
    }
    (*out)[(*len)++] = c;
    (*out)[*len] = '\0';
    return 0;
}

static int out_append_str_trunc_token(char **out, size_t *len, size_t *cap, const char *s, size_t *token_len){
    if (!s){
        s = "";
    }
    for (int i=0; s[i]!='\0'; i++){
        if (*token_len < MAX_STR_LEN){
            if (out_append_char(out, len, cap, s[i])==-1){
                return -1;
            }
            (*token_len)++;
        }else{
            // do nothing
        }
    }
    return 0;
}

//------------------
void vars_init(var_table_t *t){
    t->arr = NULL;
    t->len = 0;
    t->cap = 0;
}

void vars_destroy(var_table_t *t){
    if (!t){
        return;
    }
    for (size_t i=0; i<t->len; i++){
        free(t->arr[i].name);
        free(t->arr[i].value);
    }
    free(t->arr);
    t->arr = NULL;
    t->len = 0;
    t->cap = 0;
}

const char *vars_get(const var_table_t *t, const char *name){
    if (!t || !name){
        return NULL;
    }
    for(size_t i=0; i<t->len; i++){
        if (strcmp(t->arr[i].name, name)==0){
            return t->arr[i].value;
        }
    }
    return NULL;
}

int set_variable(var_table_t *t, const char *name, const char* value){
    if (!t || !name){
        return -1;
    }
    // replace if it exists
    for (size_t i = 0; i < t->len; i++) {
        if (strcmp(t->arr[i].name, name) == 0) {
            char *new_val = xstrdup(value);
            if (!new_val) return -1;
            free(t->arr[i].value);
            t->arr[i].value = new_val;
            return 0;
        }
    }
    // append it
    if (ensure_cap(t, t->len + 1) == -1){
        return -1;
    }

    char *new_name = xstrdup(name);
    char *new_val  = xstrdup(value);

    if (!new_name || !new_val) {
        free(new_name);
        free(new_val);
        return -1;
    }

    t->arr[t->len].name = new_name;
    t->arr[t->len].value = new_val;
    t->len += 1;

    return 0;
}

// now for expansion rules implemented: 
// - $name ends at whitespace, end of string, or another '$'
// - undefined -> empty string
// - token length capped at 128 by truncation per token
// - expanded line can be arbitrarily long
// etc

char *expand_line(const char* input, const var_table_t *t){
    if (!input) return xstrdup("");

    char *out = NULL;
    size_t out_len = 0;
    size_t out_cap = 0;

    size_t token_len = 0; /* per-token produced length */

    for (size_t i = 0; input[i] != '\0'; ) {
        char c = input[i];

        if (is_ws(c)) {
            // whitespace ends a token input
            if (out_append_char(&out, &out_len, &out_cap, c) == -1) {
                free(out);
                return NULL;
            }
            token_len = 0;
            i++;
            continue;
        }

        if (c == '$') {
            // parse variable name: [i+1, j)
            size_t j = i + 1;
            while (input[j] != '\0' && !is_ws(input[j]) && input[j] != '$') {
                j++;
            }

            // empty name => expand to empty
            char namebuf[MAX_STR_LEN + 1];
            size_t nlen = j - (i + 1);
            if (nlen > MAX_STR_LEN) nlen = MAX_STR_LEN;
            memcpy(namebuf, input + i + 1, nlen);
            namebuf[nlen] = '\0';

            const char *val = (nlen == 0) ? "" : vars_get(t, namebuf);
            if (!val) {
                val = "";
            }
            if (out_append_str_trunc_token(&out, &out_len, &out_cap, val, &token_len) == -1) {
                free(out);
                return NULL;
            }

            i = j;
            continue;
        }

        // normal character
        if (token_len < MAX_STR_LEN) {
            if (out_append_char(&out, &out_len, &out_cap, c) == -1) {
                free(out);
                return NULL;
            }
            token_len++;
        } else {
            // truncate token: skip 
        }
        i++;
    }

    if (!out) {
        return xstrdup("");
    }
    return out;
}
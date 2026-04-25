#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <dirent.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <errno.h>

#include "builtins.h"
#include "io_helpers.h"
#include "network.h"


// ====== Command execution =====

/* Return: index of builtin or -1 if cmd doesn't match a builtin
 */
bn_ptr check_builtin(const char *cmd) {
    ssize_t cmd_num = 0;
    while (cmd_num < BUILTINS_COUNT &&
           strncmp(BUILTINS[cmd_num], cmd, MAX_STR_LEN) != 0) {
        cmd_num += 1;
    }
    return BUILTINS_FN[cmd_num];
}


// ===== Builtins =====

/* Prereq: tokens is a NULL terminated sequence of strings.
 * Return 0 on success and -1 on error ... but there are no errors on echo. 
 */
ssize_t bn_echo(char **tokens) {
    ssize_t index = 1;

    // tokens[0] should be echo? cant i just do this in one loop
    while (tokens[index] != NULL) {
        // TODO:
        display_message(tokens[index]);
        if (tokens[index + 1] != NULL) {
            display_message(" "); // display nothing
        }
        index += 1;
    }
    display_message("\n");

    return 0;
}

// == bn_cd helpers ==
/*
expand "..." equivalent to  "../.." path
dots_token: string of only "." characters
out: buffer  write result into it
N dots => N-1 ".." segments joined by "/"
1 dot => . (current dir)
2 dot => ".."
3 dot => "../.."
*/
static int expand_dots(const char *dots_token, char *out, size_t out_size){
    size_t n = strlen(dots_token);
    // check its all dots
    for (size_t k=0;k<n;k++){
        if (dots_token[k] != '.'){
            return -1;
        }
    }

    if (n==1){
        if (out_size < 2){
            return -1;
        }
        out[0] = '.'; out[1] = '\0';
        return 0;
    }
    // n-1 reps of ".." joined by "/"
    size_t needed = (n-1) * 2 + (n-2) + 1;
    if (needed > out_size){
        return -1;
    }
    size_t pos = 0;
    for (size_t k=0;k<n-1;k++){
        if (k>0){
            out[pos++] = '/';
        }
        out[pos++] = '.';
        out[pos++] = '.';
    }
    out[pos] = '\0';
    return 0;
}

/*
check if a path component entirely made of dots
*/
static int is_all_dots(const char *s){
    if (!s || s[0] == '\0'){
        return 0;
    }
    for (size_t i=0;s[i]!='\0';i++){
        if (s[i] != '.'){
            return 0;
        }
    }
    return 1;
}

/*
transform a path that may contain mult-dot components such as ... or ....
into a normal path with only "." and ".." parts
eg) "../../.../" into "../../../"
write the result into out, return 0 on success, -1 on overflow?
*/
static int normalize_dots_path(const char *path, char *out, size_t out_size){
    // using a mutable copy
    size_t plen = strlen(path);
    char *temp = malloc(plen+1);
    if (!temp){
        return -1;
    }
    memcpy(temp, path, plen+1);
    // result buffer, built it in increments
    char result[MAX_STR_LEN*8];
    result[0] = '\0';
    size_t rlen = 0;

    // keep the leading slash for abs paths
    int absolute = (path[0] == '/');

    char *saveptr = NULL;
    char *component = strtok_r(temp, "/", &saveptr);
    int first = 1;

    while(component != NULL){
        char expanded[MAX_STR_LEN*4];
        if (is_all_dots(component)){
            if (expand_dots(component, expanded, sizeof(expanded))!=0){
                free(temp);
                return -1;
            }
        }else{
            size_t clen = strlen(component);
            if (clen >= sizeof(expanded)){
                free(temp);
                return -1;
            }
            memcpy(expanded, component, clen+1);
        }
        // now append the seperator
        size_t elen = strlen(expanded);
        size_t sep = (!first || absolute) ? 1 : 0;
        if (rlen + sep + elen + 1 > sizeof(result)){
            free(temp);
            return -1;
        }
        if (!first){
            result[rlen++] = '/';
        }
        memcpy(result + rlen, expanded, elen + 1);
        rlen += elen;
        first = 0;

        component = strtok_r(NULL, "/", &saveptr);
    }
    free(temp);

    // prepend again slash for absolute paths
    if (absolute){
        if (rlen + 2 > out_size){
            return -1;
        }
        out[0] = '/';
        memcpy(out + 1, result, rlen + 1);
    }else{
        if (rlen + 1 > out_size){
            return -1;
        }
        memcpy(out, result, rlen + 1);
    }

    return 0;
}



// == bn_ls helpers ==
/*
expand a path + "/" + entry name into a buffer, return 0 on success, -1 if overflow
*/
static int build_path(const char *dir, const char *name, char *out, size_t out_size){
    size_t d_len = strnlen(dir, MAX_STR_LEN*4);
    size_t n_len = strnlen(name, MAX_STR_LEN*4);
    //dir + "/" +name + '\0'
    if (d_len+1 + n_len+1 > out_size){
        return -1;
    }
    memcpy(out, dir, d_len);
    out[d_len] = '/';
    memcpy(out+d_len+1, name, n_len+1);
    return 0;
}

// == recursive ls ==
/*
path - directory to list
show_all (--a) - display all hidden files
filter (--f) - if not null, prints only names that contain thsi substring
recursive (--rec) - indicate a recursive ls traversal
max_depth - max depth remaining
cur_depth - current depth
*/
static int ls_dir(const char *path, int show_all, const char *filter, int recursive, int max_depth, int cur_depth){
    DIR *dp = opendir(path);
    if (!dp){
        display_error("ERROR: Invalid path", "");
        return -1;
    }

    struct dirent *entry; // from opendir man page ***** using dirent
    while ((entry = readdir(dp)) != NULL){
        const char *name = entry->d_name;
        
        // . and .. are special: always print, never recurse into them
        int is_dot = (strcmp(name, ".") == 0 || strcmp(name, "..") == 0);

        // Hidden entries start with '.' but are NOT . or ..
        int is_hidden = (!is_dot && name[0] == '.');

        // Skip hidden entries unless --a was given 
        if (is_hidden && !show_all) {
            continue;
        }
        
        //substring filter
        if (filter != NULL && strstr(name, filter) == NULL){
            // recurse to subdirectories even though if its filtered out already
            if (recursive){
                char child_path[MAX_STR_LEN*8];
                if (build_path(path, name, child_path, sizeof(child_path))==0){
                    struct stat st; // ask os for data ab a file or directory
                    if (stat(child_path, &st)==0 && S_ISDIR(st.st_mode)){
                        if (max_depth < 0 || cur_depth < max_depth){
                            ls_dir(child_path, show_all, filter, recursive, max_depth, cur_depth+1);
                        }
                    }
                }
            }
            continue;
        }
        
        display_message((char *)name);
        display_message("\n");

        // in case we need to recurse again,
        if (!is_dot && recursive) {
            char child_path[MAX_STR_LEN * 8];
            if (build_path(path, name, child_path, sizeof(child_path)) == 0) {
                struct stat st;
                if (stat(child_path, &st) == 0 && S_ISDIR(st.st_mode)) {
                    if (max_depth < 0 || cur_depth < max_depth) {
                        ls_dir(child_path, show_all, filter, recursive,
                               max_depth, cur_depth + 1);
                    }
                }
            }
        }
    }
    closedir(dp);
    return 0;
}

/*
ls path, --a, --f substring, --rec, --d depth
*/
ssize_t bn_ls(char **tokens){
    const char *path = ".";
    int show_all = 0;
    const char *filter =NULL;
    int recursive =0;
    int has_depth=0;
    int max_depth=-1;

    //parse the tokens
    int i = 1;
    while(tokens[i] != NULL){
        if(strncmp(tokens[i], "--a", MAX_STR_LEN)==0){
            show_all = 1;
        }else if(strncmp(tokens[i], "--rec", MAX_STR_LEN)==0){
            recursive = 1;
        }else if(strncmp(tokens[i], "--f", MAX_STR_LEN)==0){
            i++;
            if(tokens[i]==NULL){
                display_error("ERROR: Builtin failed: ", "ls");
                return -1;
            }
            filter = tokens[i];
        }else if(strncmp(tokens[i], "--d", MAX_STR_LEN)==0){
            i++;
            if(tokens[i]==NULL){
                display_error("ERROR: Builtin failed: ", "ls");
                return -1;
            }
            // now parse to find the depth, must be nonnegative
            char *endptr;
            long depth_val = strtol(tokens[i], &endptr, 10);
            if (*endptr != '\0' || depth_val < 0){
                display_error("ERROR: Builtin failed: ", "ls");
                return -1;
            }
            max_depth = (int)depth_val;
            has_depth = 1;
        }else{
            // last case has to be the path, only 1 positional argument allowed
            if (strncmp(path, ".", MAX_STR_LEN) != 0){
                display_error("ERROR: Too many arguments: ls takes a single ", "path");
                return -1;
            }
            path = tokens[i];
        }
        i++;
    }
    if (has_depth && !recursive){
        display_error("ERROR: Builtin failed: ", "ls");
        return -1;
    }

    char norm_path[MAX_STR_LEN * 8];
    if (normalize_dots_path(path, norm_path, sizeof(norm_path)) != 0) {
        display_error("ERROR: Invalid path", "");
        return -1;
    }

    return (ssize_t)ls_dir(norm_path, show_all, filter, recursive, max_depth, 0);
}

/*
cd path
No path => $HOME
*/
ssize_t bn_cd(char **tokens){
    // count # args
    int argc = 0;
    while (tokens[argc] != NULL){
        argc++;
    }

    if (argc > 2){
        display_error("ERROR: Too many arguments: cd takes a single ", "path");
        return -1;
    }

    const char *target;
    if (argc == 1|| tokens[1] == NULL){
        target = getenv("HOME");
        if (!target){
            display_error("ERROR: Builtin failed: ", "cd");
            return -1;
        }
    }else{
        target = tokens[1];
    }

    // normalize multi-dot case
    char norm[MAX_STR_LEN*8];
    if (normalize_dots_path(target, norm, sizeof(norm)) != 0){
        display_error("ERROR: Invalid path", "");
        return -1;
    }
    if (chdir(norm) != 0){
        display_error("ERROR: Invalid path", "");
        return -1;
    }
    return 0;
}

// == bn_cat ==
ssize_t bn_cat(char **tokens){
    
    if (tokens[2] != NULL){
        display_error("ERROR: Too many arguments: cat takes a single ", "file");
        return -1;
    }

    int use_stdin = (tokens[1] == NULL);

    if (use_stdin && isatty(STDIN_FILENO)){
        display_error("ERROR: No input source provided", "");
        return -1;
    }

    char buf[4096];
    size_t n;
    if (use_stdin){
        while ((n = read(STDIN_FILENO, buf, sizeof(buf))) > 0){
        write(STDOUT_FILENO, buf, n);
    }
    }else{
        FILE *fp = fopen(tokens[1], "r");
        if (!fp){
            display_error("ERROR: Cannot open file", "");
            return -1;
        }
        while ((n = fread(buf, 1, sizeof(buf), fp)) > 0){
            write(STDOUT_FILENO, buf, n);
        }
        fclose(fp);
    }
    return 0;
}

// == bn_wc ==
/*
wc filez
Counts: words, characters, newlines
Must not use string methods for counting
*/
ssize_t bn_wc(char **tokens){
    
    if (tokens[2] != NULL){
        display_error("ERROR: Too many arguments: wc takes a single ", "file");
        return -1;
    }

    int use_stdin = (tokens[1] == NULL);

    if (use_stdin && isatty(STDIN_FILENO)){
        display_error("ERROR: No input source provided", "");
        return -1;
    }

    long word_count = 0;
    long char_count = 0;
    long newline_count = 0;
    long in_word = 0;
    int c;

    if (use_stdin){
        // Read from stdin (pipe) — use read() byte by byte
        char buf[4096]; // increased capacity, wc was reading byte by byte, too slow for large pipes
        ssize_t n;
        while ((n = read(STDIN_FILENO, buf, sizeof(buf))) > 0){
            for (ssize_t k=0; k<n;k++){
                c = (unsigned char)buf[k];
                char_count++;
                int is_space = (c == ' ' || c == '\t' || c == '\n' || c == '\r');
                if (c == '\n'){
                    newline_count++;
                }
                if (!is_space){
                    if (!in_word){ word_count++; in_word = 1; }
                } else {
                    in_word = 0;
                }
            }
        }
    }else{
        FILE *fp = fopen(tokens[1], "r");
        if (!fp){
            display_error("ERROR: Cannot open file", "");
            return -1;
        }
        while ((c = fgetc(fp)) != EOF){
        char_count++;
        // whitespace count without string methods
        int is_space = (c == ' ' || c == '\t' || c == '\n' || c == '\r');
        if (c == '\n'){
            newline_count++;
        }
        if (!is_space){
            if (!in_word){
                word_count++;
                in_word = 1;
            }
        }else{
            in_word = 0;
        }
    }
    fclose(fp);
    }

    // now build and display output
    char num_buf[64];

    display_message("word count ");
    snprintf(num_buf, sizeof(num_buf), "%ld", word_count);
    display_message(num_buf);
    display_message("\n");

    display_message("character count ");
    snprintf(num_buf, sizeof(num_buf), "%ld", char_count);
    display_message(num_buf);
    display_message("\n");

    display_message("newline count ");
    snprintf(num_buf, sizeof(num_buf), "%ld", newline_count);
    display_message(num_buf);
    display_message("\n");

    return 0;
}

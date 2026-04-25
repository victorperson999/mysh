#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#include "builtins.h"
#include "commands.h"
#include "io_helpers.h"
#include "variables.h"
#include "network.h"

var_table_t *g_vars_ptr = NULL;

// You can remove __attribute__((unused)) once argc and argv are used.
int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    char *prompt = "mysh$ ";

    char input_buf[MAX_STR_LEN + 1];
    input_buf[MAX_STR_LEN] = '\0';
    char *token_arr[MAX_STR_LEN+1];

    // add the variable tables (m2 change)
    var_table_t vars;
    vars_init(&vars);
    g_vars_ptr = &vars;

    commands_init();
    network_init();

    while (1) {
        bg_check_done(&g_bg);
        // Prompt and input tokenization
        // Display the prompt via the display_message function.
        display_message(prompt);

        ssize_t ret = get_input(input_buf);

        if (ret == -2){ // clean exit on ctrl D
            break;
        }
        if (ret <0 ){ // error on EINTR
            continue;
        }
        if (ret == 0){ // empty line (reprompt)
            continue;
        }

        char raw_line[MAX_STR_LEN + 1];
        strncpy(raw_line, input_buf, MAX_STR_LEN+1);
        raw_line[MAX_STR_LEN] = '\0';

        size_t token_count = tokenize_input(input_buf, token_arr);
        if (token_count == 0){ // if we have blank line, reprompt
            continue;
        }

        // treat assignment only on original input (not after expansion)
        char *eq = strchr(token_arr[0], '=');
        int valid_assignment = 0;
        if (eq != NULL && token_count == 1){
            size_t nlen = (size_t)(eq - token_arr[0]);
            if (nlen>0 && nlen<=MAX_STR_LEN){
                valid_assignment = 1;
                for (size_t k=0; k<nlen; k++){
                    char ch = token_arr[0][k];
                    if (!((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') ||
                        (ch >= '0' && ch <= '9') || ch == '_')) {
                        valid_assignment = 0;
                        break;
                    }
                }
            }
        }
        if (valid_assignment){ // second case pass through
            size_t name_len = (size_t)(eq - token_arr[0]);

            if (name_len > MAX_STR_LEN){
                name_len = MAX_STR_LEN;
            }

            char name[MAX_STR_LEN+1];
            memcpy(name, token_arr[0], name_len);
            name[name_len] = '\0';

            const char *value_raw = eq + 1;

            // allow for expansions inside rhs value
            char *value_expanded = expand_line(value_raw, &vars);
            if (!value_expanded){
                display_error("ERROR: out of memory: ", "expand");
                continue;
            }
            if (set_variable(&vars, name, value_expanded) == -1){
                free(value_expanded);
                display_error("ERROR: out of memory: ", "set");
                continue;
            }
            free(value_expanded);
            continue;
        }

        // variable expand the whole line
        char *expanded = expand_line(raw_line, &vars);
        if (!expanded){
            display_error("ERROR: out of memory: ", "expand");
            continue;
        }

        // strip trailing
        int background = 0;
        {
            size_t elen = strlen(expanded);
            //Find last non-whitespace character
            size_t last = elen;
            while (last > 0 && (expanded[last-1] == ' '  ||
                                 expanded[last-1] == '\t' ||
                                 expanded[last-1] == '\n')) {
                last--;
            }
            if (last > 0 && expanded[last - 1] == '&') {
                background = 1;
                expanded[last - 1] = '\0'; // strip the & 
                //strip any whitespace before the & 
                size_t new_end = last - 1;
                while (new_end > 0 && (expanded[new_end-1] == ' '  ||
                                       expanded[new_end-1] == '\t' ||
                                       expanded[new_end-1] == '\n')) {
                    expanded[--new_end] = '\0';
                }
            }
        }

        // full_cmd is the expanded line without & — used for Done messages
        char full_cmd[MAX_STR_LEN + 1];
        strncpy(full_cmd, expanded, MAX_STR_LEN);
        full_cmd[MAX_STR_LEN] = '\0';

        /* ---- Split expanded on '|' into segments ----
         * '|' may appear with or without surrounding spaces (e.g. "cat f|wc").
         * We scan character by character and replace '|' with '\0'.
         * seg_strs[i] points into expanded directly.
         */
        char *seg_strs[MAX_PIPE_SEGMENTS];
        int seg_count = 0;
        seg_strs[seg_count++] = expanded;

        for (char *p = expanded; *p != '\0'; p++) {
            if (*p == '|') {
                *p = '\0';                              //terminate current segment
                if (seg_count < MAX_PIPE_SEGMENTS) {
                    seg_strs[seg_count++] = p + 1;     //next segment starts after | 
                }
            }
        }

        /* ---- Tokenize each segment ---- */
        // seg_tokens[i] is the NULL-terminated token array for segment i
        char *seg_tokens[MAX_PIPE_SEGMENTS][MAX_STR_LEN + 1];
        int seg_tok_counts[MAX_PIPE_SEGMENTS];

        int empty_segment = 0;
        for (int i=0; i < seg_count;i++) {
            seg_tok_counts[i] = (int)tokenize_input(seg_strs[i], seg_tokens[i]);
            if (seg_tok_counts[i] == 0) {
                empty_segment = 1;
            }
        }

        if (empty_segment) {
            // ex) "| wc" or "cat |" — ignore silently
            free(expanded);
            continue;
        }

        //exit: only valid as a single foreground command
        if (seg_count == 1 && !background &&
            strcmp(seg_tokens[0][0], "exit") == 0) {
            // clean server befor exit
            if (g_server.active){
                char *close_tokens[] = {"close-server", NULL};
                bn_close_server(close_tokens);
            }
            free(expanded);
            break;
        }

        /* ---- cd: must run in the parent process ----
         * chdir() only affects the calling process, so forking it is useless.
         * Only run in parent when it's a single foreground command.
         */
        if (seg_count == 1 && !background &&
            strcmp(seg_tokens[0][0], "cd") == 0) {
            bn_cd(seg_tokens[0]);
            free(expanded);
            continue;
        }
        // network commands ***
        if (seg_count == 1 && !background &&
            strcmp(seg_tokens[0][0], "start-server") == 0) {
            bn_start_server(seg_tokens[0]);
            free(expanded);
            continue;
        }
        if (seg_count == 1 && !background &&
            strcmp(seg_tokens[0][0], "close-server") == 0) {
            bn_close_server(seg_tokens[0]);
            free(expanded);
            continue;
        }
        if (seg_count == 1 && !background &&
            strcmp(seg_tokens[0][0], "send") == 0) {
            bn_send(seg_tokens[0]);
            free(expanded);
            continue;
        }
        if (seg_count == 1 && !background &&
            strcmp(seg_tokens[0][0], "start-client") == 0) {
            bn_start_client(seg_tokens[0]);
            free(expanded);
            continue;
        }

        //Build segment pointer array for execute_pipeline
        char **segment_ptrs[MAX_PIPE_SEGMENTS];
        for (int i = 0; i < seg_count; i++) {
            segment_ptrs[i] = seg_tokens[i];
        }

        // finally execute
        execute_pipeline(segment_ptrs, seg_tok_counts, seg_count,
                         &vars, &g_bg, background, full_cmd);
        
        free(expanded);
    }

    vars_destroy(&vars);
    bg_destroy(&g_bg);

    // need to close server if running still
    if (g_server.active){
        char *close_tokens[] = {"close-server", NULL};
        bn_close_server(close_tokens);
    }

    return 0;
}

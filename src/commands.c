#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <errno.h>
#include <stdio.h>

#include "commands.h"
#include "builtins.h"
#include "io_helpers.h"
#include "variables.h"

// make the global background table
bg_table_t g_bg;
static int g_job_counter = 0;

// init the shell
static void sigint_handler(int sig) {
    (void)sig;
    write(STDOUT_FILENO, "\n", 1);
}

void commands_init(void){
    bg_init(&g_bg);
    struct sigaction sa;
    sa.sa_handler = sigint_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;  /* NO SA_RESTART — want syscalls interrupted */
    sigaction(SIGINT, &sa, NULL);
}

// table operations
void bg_init(bg_table_t *t){
    t->jobs = NULL;
    t->len = 0;
    t->cap = 0;
}

void bg_destroy(bg_table_t *t){
    free(t->jobs);
    t->jobs = NULL;
    t->len = 0;
    t->cap = 0;
}

static int bg_ensure_cap(bg_table_t *t){
    if (t->len < t->cap){
        return 0;
    }
    size_t new_cap = (t->cap == 0) ? 8 : t->cap * 2;
    bg_job_t *p = realloc(t->jobs, new_cap *sizeof(bg_job_t));
    if (!p){
        return -1;
    }

    t->jobs = p;
    t->cap = new_cap;
    return 0;
}

int bg_add(bg_table_t *t, pid_t *pids, char (*cmds)[MAX_STR_LEN+1], size_t proc_count, const char *full_cmd){
    if (bg_ensure_cap(t) != 0){
        return -1;
    }
    g_job_counter++;
    bg_job_t *job = &t->jobs[t->len++];

    job->number = g_job_counter;
    job->proc_count = proc_count;
    job->done_count = 0;
    job->reported = 0;

    strncpy(job->full_cmd, full_cmd, MAX_STR_LEN);
    job->full_cmd[MAX_STR_LEN] = '\0';

    for (size_t i=0;i<proc_count; i++){
        job->procs[i].pid = pids[i];
        strncpy(job->procs[i].cmd, cmds[i], MAX_STR_LEN);
        job->procs[i].cmd[MAX_STR_LEN] = '\0';
    }

    return job->number;
}

void bg_mark_done(bg_table_t *t, pid_t pid) {

    for (size_t i = 0; i < t->len; i++) {

        bg_job_t *job = &t->jobs[i];
        for (size_t j = 0;j < job->proc_count;j++) {
            if (job->procs[j].pid == pid) {
                job->done_count++;
                return;
            }
        }
    }
}

void bg_print_done(bg_table_t *t) {

    char buf[MAX_STR_LEN * 4];
    size_t i = 0;

    while (i < t->len) {

        bg_job_t *job = &t->jobs[i];

        if (job->done_count >= job->proc_count && !job->reported) {
            snprintf(buf, sizeof(buf), "[%d]+ Done %s\n",
                     job->number, job->full_cmd);
            display_message(buf);
            for (size_t k = i;k < t->len - 1;k++) {
                t->jobs[k] = t->jobs[k + 1];
            }
            t->len--;

            if (t->len == 0) {
                g_job_counter = 0;
            }
        } else {
            i++;
        }
    }
}

void bg_check_done(bg_table_t *t) {

    pid_t pid;
    int status;

    while ((pid = waitpid(-1, &status, WNOHANG)) > 0) {
        bg_mark_done(t, pid);
    }
    bg_print_done(t);
}

// outside command search 

static void exec_external(char **tokens) {
    char path[MAX_STR_LEN + 16];

    snprintf(path, sizeof(path), "/bin/%s", tokens[0]);
    execv(path, tokens);
    snprintf(path, sizeof(path), "/usr/bin/%s", tokens[0]);
    execv(path, tokens);

    display_error("ERROR: Unknown command: ", tokens[0]);

    exit(1);
}

// pipeline exec
void execute_pipeline(char ***segments, int *seg_counts, int seg_count, var_table_t *vars,
                      bg_table_t *bg, int background, const char *full_cmd) {

    (void)seg_counts;
    (void)vars;

    //1: Create all pipes
    int pipes[MAX_PIPE_SEGMENTS - 1][2];

    for (int i=0;i<seg_count - 1;i++) {
        if (pipe(pipes[i]) == -1) {
            display_error("ERROR: Builtin failed: ", "pipe");
            return;
        }
    }

    pid_t pids[MAX_PIPE_SEGMENTS];
    char  cmds[MAX_PIPE_SEGMENTS][MAX_STR_LEN + 1];

    //2: Fork one child per segment
    for (int i = 0; i < seg_count; i++) {
        char **tokens = segments[i];

        strncpy(cmds[i], tokens[0], MAX_STR_LEN);
        cmds[i][MAX_STR_LEN] = '\0';

        pid_t pid = fork(); // fork ***

        if (pid < 0) {
            display_error("ERROR: Builtin failed: ", "fork");
            for (int j=0;j < seg_count - 1;j++) {
                close(pipes[j][0]);
                close(pipes[j][1]);
            }
            return;
        }

        if (pid == 0) {
            // Child: restore SIGINT so Ctrl+C kills it
            signal(SIGINT, SIG_DFL);

            // Wire stdin
            if (i == 0) {
                if (background) {
                    int devnull = open("/dev/null", O_RDONLY);
                    if (devnull >= 0) {
                        dup2(devnull, STDIN_FILENO);
                        close(devnull);
                    }
                }
            } else {
                dup2(pipes[i - 1][0], STDIN_FILENO);
            }

            // Wire stdout
            if (i < seg_count - 1) {
                dup2(pipes[i][1], STDOUT_FILENO);
            }

            // Close ALL pipe fds, since we dup2 what we needed
            for (int j=0;j < seg_count - 1;j++) {
                close(pipes[j][0]);
                close(pipes[j][1]);
            }

            // Run builtin or external
            bn_ptr fn = check_builtin(tokens[0]);
            if (fn != NULL) {
                ssize_t ret = fn(tokens);
                exit(ret == -1 ? 1 : 0);
            }

            exec_external(tokens);
            exit(1);
        }

        pids[i] = pid;
    }

    //3: Parent closes ALL pipe fds
    // until parent closes write ends, readers block forever
    for (int i=0;i < seg_count - 1;i++) {
        close(pipes[i][0]);
        close(pipes[i][1]);
    }

    //4: Background or foreground
    if (background) {
        int job_num = bg_add(bg, pids, cmds, (size_t)seg_count, full_cmd);
        
        if (job_num > 0) {
            char buf[MAX_STR_LEN];
            snprintf(buf, sizeof(buf), "[%d] %d\n",
                     job_num, (int)pids[seg_count - 1]);
            display_message(buf);
        }
    } else {
        for (int i=0;i < seg_count;i++) {
        int status;
        while (waitpid(pids[i], &status, 0) == -1) {
            if (errno == EINTR) {
                /* SIGINT interrupted the wait — kill the child and keep waiting */
                kill(pids[i], SIGINT);
            } else {
                break;
            }
        }
    }
    }
}

// table methods
ssize_t bn_ps(char **tokens) {

    (void)tokens;
    char buf[MAX_STR_LEN * 2];

    for (size_t i=0;i < g_bg.len;i++) {
        bg_job_t *job = &g_bg.jobs[i];
        for (size_t j=0;j < job->proc_count;j++) {
            snprintf(buf, sizeof(buf), "%s %d\n", job->procs[j].cmd, (int)job->procs[j].pid);
            display_message(buf);
        }
    }
    return 0;
}

ssize_t bn_kill(char **tokens) {
    if (tokens[1] == NULL) {
        display_error("ERROR: Builtin failed: ", "kill");
        return -1;
    }

    char *endptr;
    long pid_val = strtol(tokens[1], &endptr, 10);
    if (*endptr != '\0') {
        display_error("ERROR: The process does not exist", "");
        return -1;
    }

    int signum = SIGTERM;
    if (tokens[2] != NULL) {
        long sig_val = strtol(tokens[2], &endptr, 10);
        if (*endptr != '\0' || sig_val < 1 || sig_val > 64) {
            display_error("ERROR: Invalid signal specified", "");
            return -1;
        }
        signum = (int)sig_val;
    }

    if (kill((pid_t)pid_val, signum) != 0) {
        if (errno == ESRCH) {
            display_error("ERROR: The process does not exist", "");
        } else if (errno == EINVAL) {
            display_error("ERROR: Invalid signal specified", "");
        } else {
            display_error("ERROR: Builtin failed: ", "kill");
        }
        return -1;
    }

    return 0;
}
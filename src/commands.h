#ifndef __COMMANDS_H__
#define __COMMANDS_H__

#include <sys/types.h>
#include <unistd.h>
#include "io_helpers.h"
#include "variables.h"
#include "builtins.h"

#define MAX_PIPE_SEGMENTS 64

// 1 process within a job.
typedef struct {
    pid_t pid;
    char cmd[MAX_STR_LEN+1];
} bg_proc_t;

// a single job corresponds to one user command line (maybe another pipe)
// use a fixed size proc array to avoid nested dynamic allocation

typedef struct {
    int number;
    char full_cmd[MAX_STR_LEN+1]; // full line for done message
    bg_proc_t procs[MAX_PIPE_SEGMENTS]; // 1 entry per pipe
    size_t proc_count; // how many processes?
    size_t done_count;
    int reported;
} bg_job_t;

// set up table of all active background jobs by this given shell, store as dynamic array in commands.c
typedef struct {
    bg_job_t *jobs;
    size_t len;
    size_t cap;    
} bg_table_t;


extern bg_table_t g_bg;

// declare the methods
void bg_init(bg_table_t *t);
void bg_destroy(bg_table_t *t);

// add a new job to the table?
// pids are parallell arrays of length proc_count (process count)
// full cmd is the raw command line string
// returns the job number assigned, or -1 on oom
int bg_add(bg_table_t *t, pid_t *pids, char (*cmds)[MAX_STR_LEN+1], 
           size_t proc_count, const char *full_cmd);


// mark a pid, called from sigchild handler. Its safe to call with a pid not in the table.
void bg_mark_done(bg_table_t *t, pid_t pid);

// print [n] + done <cmd> for every completed job and then remove them.
// call this before printing each prompt, resets job counter when the table is empty
void bg_print_done(bg_table_t *t);

// ***PIPELINE EXECUTION***
// segments: array of token arrays, once per pipe stage. eg: {{"cat","file",NULL}, {"wc",NULL}}
// seg_counts: number of tokens in each segment
// seg_count: number of segments (no pipe = 1)
// vars: variable table
// bg: background job table
// background: 1 if the job should run in the background
// full_cmd: original raw command string for done and job messages
void execute_pipeline(char ***segments, int *seg_counts, int seg_count,
                      var_table_t *vars, bg_table_t *bg, int background, const char *full_cmd);

                
// for builtins  that need access to the global bg_table so theyre coded in commands.c,
// over builtins.c, matching bn_ptr
ssize_t bn_ps(char **tokens);
ssize_t bn_kill(char **tokens);

void commands_init(void);
void bg_check_done(bg_table_t *t);


#endif
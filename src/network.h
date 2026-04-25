#ifndef __NETWORK_H__
#define __NETWORK_H__

#include <sys/types.h>
#include "io_helpers.h"

/*
 * Shell-side server state — parent only needs to know if server
 * is running, what pid the child is, and what port it's on.
 * The full client list and fd_sets live inside the server child.
 */
typedef struct {
    int   active;
    pid_t server_pid;
    int   port;
} shell_server_t;

extern shell_server_t g_server;

/* Call once from main() before the loop */
void network_init(void);

/* No server_poll() needed — server runs in its own child process */

ssize_t bn_start_server(char **tokens);
ssize_t bn_close_server(char **tokens);
ssize_t bn_send(char **tokens);
ssize_t bn_start_client(char **tokens);

#endif 
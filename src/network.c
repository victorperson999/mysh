#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <sys/wait.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <errno.h>
#include <signal.h>
#include <time.h>
#include <fcntl.h>

#include "network.h"
#include "chat_helpers.h"
#include "socket.h"
#include "io_helpers.h"
#include "variables.h"

extern var_table_t *g_vars_ptr;

/* Shell-side global — just tracks the child pid and port */
shell_server_t g_server;

/* Used inside the server child to handle SIGTERM cleanly */
static volatile int server_should_exit = 0;
static void server_sigterm_handler(int sig) {
    (void)sig;
    server_should_exit = 1;
}


/*
 * network_init:
 * Called once from main() before the shell loop starts.
 */
void network_init(void) {
    g_server.active = 0;
    g_server.server_pid = -1;
    g_server.port = -1;
    signal(SIGPIPE, SIG_IGN);
}


/*
 * Runs entirely inside the forked server child process.
 * Mirrors chat_server.c's main loop:
 *   - Accepts new connections, assigns IDs
 *   - Reads messages, handles \connected, broadcasts
 *   - Exits on SIGTERM
 *
 * Uses a full blocking select() — this is fine because it's
 * in its own process and never blocks the shell.
 */
static void run_server_child_with_socket(struct listen_sock ls) {
    signal(SIGPIPE, SIG_IGN);

    struct sigaction sa;
    sa.sa_handler = server_sigterm_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGTERM, &sa, NULL);

    struct server_state srv;
    srv.sock              = ls;
    srv.clients           = NULL;
    srv.total_connected   = 0;
    srv.current_connected = 0;
    srv.active            = 1;
    srv.max_fd            = ls.sock_fd;
    FD_ZERO(&srv.all_fds);
    FD_SET(ls.sock_fd, &srv.all_fds);

    while (!server_should_exit) {
        fd_set ready = srv.all_fds;
        int nready = select(srv.max_fd + 1, &ready, NULL, NULL, NULL);

        if (server_should_exit) break;
        if (nready < 0) {
            if (errno == EINTR) continue;
            break;
        }

        /* New connection */
        if (FD_ISSET(ls.sock_fd, &ready)) {
            struct sockaddr_in peer;
            unsigned int peer_len = sizeof(peer);
            int cfd = accept(ls.sock_fd, (struct sockaddr *)&peer, &peer_len);
            if (cfd >= 0) {
                struct client_sock *nc = malloc(sizeof(struct client_sock));
                if (nc) {
                    nc->sock_fd = cfd;
                    nc->state   = 0;
                    nc->id      = 0;
                    nc->inbuf   = 0;
                    nc->next    = NULL;
                    memset(nc->buf, 0, BUF_SIZE);
                    if (srv.clients == NULL) {
                        srv.clients = nc;
                    } else {
                        struct client_sock *tail = srv.clients;
                        while (tail->next) tail = tail->next;
                        tail->next = nc;
                    }
                    srv.total_connected++;
                    srv.current_connected++;
                    assign_client_id(nc, srv.total_connected);
                    FD_SET(cfd, &srv.all_fds);
                    if (cfd > srv.max_fd) srv.max_fd = cfd;
                } else {
                    close(cfd);
                }
            }
        }

        /* Read from each client */
        struct client_sock *curr = srv.clients;
        while (curr != NULL) {
            if (!FD_ISSET(curr->sock_fd, &ready)) {
                curr = curr->next;
                continue;
            }
            int status = read_from_client(curr);
            if (status == -1 || status == 1) {
                close(curr->sock_fd);
                FD_CLR(curr->sock_fd, &srv.all_fds);
                srv.current_connected--;
                remove_client(&curr, &srv.clients);
                continue;
            }
            char *msg;
            while (get_message(&msg, curr->buf, &(curr->inbuf)) == 0) {
                if (strcmp(msg, "\\connected") == 0) {
                    char reply[64];
                    snprintf(reply, sizeof(reply), "%d", srv.current_connected);
                    write_buf_to_client(curr, reply, (int)strlen(reply));
                    free(msg);
                    continue;
                }
                char full_msg[BUF_SIZE];
                snprintf(full_msg, sizeof(full_msg), "client%d: %s", curr->id, msg);
                free(msg);
                broadcast(&srv, full_msg, (int)strlen(full_msg));
            }
            curr = curr->next;
        }
    }

    /* Cleanup */
    struct client_sock *c = srv.clients;
    while (c) {
        struct client_sock *next = c->next;
        close(c->sock_fd);
        free(c);
        c = next;
    }
    close(ls.sock_fd);
    free(ls.addr);
    _exit(0);
}


/*
 * Forks a child that runs run_server_child().
 * Parent records the pid and marks server active.
 */
ssize_t bn_start_server(char **tokens) {
    if (tokens[1] == NULL) {
        display_error("ERROR: No port provided", "");
        return -1;
    }

    char *endptr;
    long port = strtol(tokens[1], &endptr, 10);
    if (*endptr != '\0' || port < 1 || port > 65535) {
        display_error("ERROR: Builtin failed: ", "start-server");
        return -1;
    }

    if (g_server.active) {
        char *close_tokens[] = {"close-server", NULL};
        bn_close_server(close_tokens);
    }

    /* Pipe: child writes 1 byte to tell parent bind succeeded */
    int pipefd[2];
    if (pipe(pipefd) < 0) {
        display_error("ERROR: Builtin failed: ", "start-server");
        return -1;
    }

    pid_t pid = fork();
    if (pid < 0) {
        close(pipefd[0]);
        close(pipefd[1]);
        display_error("ERROR: Builtin failed: ", "start-server");
        return -1;
    }

    if (pid == 0) {
        /* Child */
        close(pipefd[0]);

        /* Suppress perror output so parent's ERROR message is first on stderr */
        int devnull = open("/dev/null", O_WRONLY);
        if (devnull >= 0) {
            dup2(devnull, STDERR_FILENO);
            close(devnull);
        }

        struct listen_sock ls;
        ls.sock_fd = -1;
        ls.addr    = NULL;
        if (setup_server_socket(&ls, (int)port) != 0) {
            char fail = 0;
            write(pipefd[1], &fail, 1);
            close(pipefd[1]);
            exit(1);
        }

        /* Tell parent: bind succeeded */
        char ok = 1;
        write(pipefd[1], &ok, 1);
        close(pipefd[1]);

        run_server_child_with_socket(ls);
        exit(0); /* unreachable */
    }

    /* Parent */
    close(pipefd[1]);

    char status_byte = 0;
    ssize_t n = read(pipefd[0], &status_byte, 1);
    close(pipefd[0]);

    if (n <= 0 || status_byte == 0) {
        /* Child failed to bind — reap it and report error */
        waitpid(pid, NULL, 0);
        display_error("ERROR: Builtin failed: ", "start-server");
        return -1;
    }

    g_server.active     = 1;
    g_server.server_pid = pid;
    g_server.port       = (int)port;

    return 0;
}


/*
 * bn_close_server:
 * Sends SIGTERM to the server child, waits for it to exit,
 * resets shell-side state.
 */
ssize_t bn_close_server(char **tokens) {
    (void)tokens;

    if (!g_server.active) {
        display_error("ERROR: Builtin failed: ", "close-server");
        return -1;
    }

    kill(g_server.server_pid, SIGTERM);

    /* Wait for server child to clean up and exit */
    int status;
    while (waitpid(g_server.server_pid, &status, 0) == -1) {
        if (errno != EINTR) break;
    }

    g_server.active     = 0;
    g_server.server_pid = -1;
    g_server.port       = -1;

    return 0;
}


/*
 * connect_to_server:
 * Helper used by both bn_send and bn_start_client.
 * Resolves hostname, connects, returns socket fd or -1 on error.
 * Also receives and frees (or returns) the assigned client ID.
 */
static int connect_to_server(int port, const char *hostname,
                              char **id_out) {
    struct hostent *hp = gethostbyname(hostname);
    if (!hp) return -1;

    int sock_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (sock_fd < 0) return -1;

    struct sockaddr_in srv;
    srv.sin_family = AF_INET;
    srv.sin_port   = htons(port);
    memcpy(&srv.sin_addr, hp->h_addr_list[0], hp->h_length);

    if (connect(sock_fd, (struct sockaddr *)&srv, sizeof(srv)) < 0) {
        close(sock_fd);
        return -1;
    }

    /* Receive assigned client ID */
    char id_buf[BUF_SIZE];
    int  id_inbuf = 0;
    int  status;
    do {
        status = read_from_socket(sock_fd, id_buf, &id_inbuf);
    } while (status == 2);

    if (status != 0) {
        close(sock_fd);
        return -1;
    }

    char *id_str = NULL;
    if (get_message(&id_str, id_buf, &id_inbuf) != 0) {
        close(sock_fd);
        return -1;
    }

    if (id_out) {
        *id_out = id_str;
    } else {
        free(id_str);
    }

    return sock_fd;
}


/*
 * bn_send:
 * One-shot: connect, receive ID, validate message length, send, close.
 */
ssize_t bn_send(char **tokens) {
    if (tokens[1] == NULL) {
        display_error("ERROR: No port provided", "");
        return -1;
    }
    if (tokens[2] == NULL) {
        display_error("ERROR: No hostname provided", "");
        return -1;
    }
    if (tokens[3] == NULL) {
        display_error("ERROR: No message provided", "");
        return -1;
    }

    char *endptr;
    long port = strtol(tokens[1], &endptr, 10);
    if (*endptr != '\0' || port < 1 || port > 65535) {
        display_error("ERROR: Builtin failed: ", "send");
        return -1;
    }

    /* Build message from tokens[3..] */
    char msg[MAX_USER_MSG + 1];
    msg[0] = '\0';
    for (int i = 3; tokens[i] != NULL; i++) {
        if (i > 3) strncat(msg, " ", MAX_USER_MSG - strlen(msg));
        strncat(msg, tokens[i], MAX_USER_MSG - strlen(msg));
    }

    /* Validate length — must be strictly less than MAX_USER_MSG */
    if ((int)strlen(msg) >= MAX_USER_MSG) {
        display_error("ERROR: Message too long", "");
        return -1;
    }

    int sock_fd = connect_to_server((int)port, tokens[2], NULL);
    if (sock_fd < 0) {
        display_error("ERROR: Builtin failed: ", "send");
        return -1;
    }

    /* Send with CRLF */
    int msg_len = (int)strlen(msg);
    char wire[MAX_USER_MSG + 2];
    memcpy(wire, msg, msg_len);
    wire[msg_len]     = '\r';
    wire[msg_len + 1] = '\n';
    write_to_socket(sock_fd, wire, msg_len + 2);

    close(sock_fd);
    return 0;
}


/*
 * Forks a child that runs the interactive client loop.
 * Parent waits (foreground — blocks shell until client disconnects).
 */
ssize_t bn_start_client(char **tokens) {
    if (tokens[1] == NULL) {
        display_error("ERROR: No port provided", "");
        return -1;
    }
    if (tokens[2] == NULL) {
        display_error("ERROR: No hostname provided", "");
        return -1;
    }

    char *endptr;
    long port = strtol(tokens[1], &endptr, 10);
    if (*endptr != '\0' || port < 1 || port > 65535) {
        display_error("ERROR: Builtin failed: ", "start-client");
        return -1;
    }

    char *id_str = NULL;
    int sock_fd = connect_to_server((int)port, tokens[2], &id_str);
    if (sock_fd < 0) {
        display_error("ERROR: Builtin failed: ", "start-client");
        return -1;
    }

    // dont  display id to stdout
    free(id_str);

    /* Run client loop directly in the shell process — no fork.
     * This avoids the stdin-sharing race where a forked child
     * consumes input meant for the parent shell. */
    fd_set all_fds;
    FD_ZERO(&all_fds);
    FD_SET(STDIN_FILENO, &all_fds);
    FD_SET(sock_fd, &all_fds);
    int max_fd = sock_fd;

    char srv_buf[BUF_SIZE];
    int  srv_inbuf = 0;

    while (1) {
        fd_set listen_fds = all_fds;
        int nready = select(max_fd + 1, &listen_fds, NULL, NULL, NULL);
        if (nready < 0) {
            if (errno == EINTR) break;   /* Ctrl+C exits client */
            break;
        }

        /* Check socket FIRST — detect server death before touching stdin */
        if (FD_ISSET(sock_fd, &listen_fds)) {
            int status = read_from_socket(sock_fd, srv_buf, &srv_inbuf);
            if (status == -1 || status == 1) break;

            char *msg;
            while (get_message(&msg, srv_buf, &srv_inbuf) == 0) {
                display_message(msg);
                display_message("\n");
                free(msg);
            }
        }

        if (FD_ISSET(STDIN_FILENO, &listen_fds)) {
            char input_buf[MAX_USER_MSG + 1];
            ssize_t n = read(STDIN_FILENO, input_buf, MAX_STR_LEN);
            if (n <= 0) break;    /* EOF (Ctrl+D) exits client */

            if (input_buf[0] == '\0') break; // null byte, signal client disconnect!

            if (input_buf[n - 1] == '\n') n--;
            input_buf[n] = '\0';

            /* Expand variables before length check */
            char *exp = expand_line(input_buf, g_vars_ptr);
            if (!exp) continue;
            int msg_len = (int)strlen(exp);

            if (msg_len >= MAX_USER_MSG) {
                display_error("ERROR: Message too long", "");
                free(exp);
                continue;
            }

            char wire[MAX_USER_MSG + 2];
            memcpy(wire, exp, msg_len);
            wire[msg_len] = '\r';
            wire[msg_len+1] = '\n';
            free(exp);

            if (write_to_socket(sock_fd, wire, msg_len + 2) != 0) {
                break;
            }
        }
    }

    close(sock_fd);
    return 0;
}
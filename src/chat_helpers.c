#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "socket.h"
#include "chat_helpers.h"
#include "io_helpers.h"

/*
 * Appends \r\n to buf and sends it over the client's socket.
 * This is the low-level send used by broadcast() and assign_client_id().
 */
int write_buf_to_client(struct client_sock *c, char *buf, int len) {
    char msg[BUF_SIZE];
    if (len + 2 > BUF_SIZE) return 1;
    memcpy(msg, buf, len);
    msg[len]     = '\r';
    msg[len + 1] = '\n';
    return write_to_socket(c->sock_fd, msg, len + 2);
}

/*
 * traverses linked list to find *curr, unlinks it, frees it.
 * Updates *curr to the next node so the caller's loop continues safely.
 * Updates *clients if we removed the head.
 */
int remove_client(struct client_sock **curr, struct client_sock **clients) {
    if (!curr || !*curr || !clients || !*clients) return 1;

    struct client_sock *target = *curr;

    if (*clients == target) {
        *clients = target->next;
        *curr = target->next;
        free(target);
        return 0;
    }

    struct client_sock *prev = *clients;
    while (prev->next != NULL && prev->next != target) {
        prev = prev->next;
    }
    if (prev->next == NULL) return 1;

    prev->next = target->next;
    *curr = target->next;
    free(target);
    return 0;
}

/*
 * Small wrapper — sends to read_from_socket() in socket.c.
 * Returns -1/0/1/2 as said in chat_helpers.h.
 */
int read_from_client(struct client_sock *curr) {
    return read_from_socket(curr->sock_fd, curr->buf, &(curr->inbuf));
}

/*
 * Called when a new client connects. Assigns the given integer id,
 * marks the client as ready (state=1), then sends "clientN:" back
 * to the client so it knows its own prefix for display.
 * Returns 0 on success, 1 if the send failed.
 */
int assign_client_id(struct client_sock *curr, int id) {
    curr->id    = id;
    curr->state = 1;

    /* Build the ID string: "client1:", "client2:", etc. */
    char id_msg[MAX_NAME + 2];
    snprintf(id_msg, sizeof(id_msg), "client%d:", id);

    /* Send it back so the client can display it as its prefix */
    if (write_buf_to_client(curr, id_msg, (int)strlen(id_msg)) != 0) {
        return 1;
    }
    return 0;
}

/*
 * Sends msg to every connected client.
 * Also prints the message to the server's own stdout (the shell console).
 * If a client's send fails with disconnect (ret==2), we remove it from
 * the list, update the fd_set, and decrement current_connected.
 * If a client's send fails with a write error (ret==1), we also remove it.
 */
void broadcast(struct server_state *server, const char *msg, int len) {
    /* Print to server console — use display_message for unbuffered output */
    char console_buf[BUF_SIZE + 2];
    snprintf(console_buf, sizeof(console_buf), "%s\n", msg);
    display_message(console_buf);

    struct client_sock *curr = server->clients;
    while (curr != NULL) {
        int ret = write_buf_to_client(curr, (char *)msg, len);
        if (ret != 0) {
            /* Failed — disconnect this client */
            close(curr->sock_fd);
            FD_CLR(curr->sock_fd, &server->all_fds);
            server->current_connected--;
            remove_client(&curr, &server->clients);
            /* remove_client advances curr to next, so loop continues */
        } else {
            curr = curr->next;
        }
    }
}
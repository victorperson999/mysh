#ifndef CHAT_HELPERS_H
#define CHAT_HELPERS_H

#include <sys/select.h>
#include "socket.h"

// Server assigns an integers id 1,2....... when the client connects
// just connected=0, id assigned=1, ready to send messages to others.
struct client_sock {
    int sock_fd;
    int state;
    int id;                  /* assigned by server on connect */
    char buf[BUF_SIZE];
    int inbuf;
    struct client_sock *next;
};

// this struct keeps track of the state of the server, client list, and keeps track of clients connected. (and was connected)
struct server_state {
    struct listen_sock sock;     /* listening socket */
    struct client_sock *clients; /* linked list of connected clients */
    int total_connected;         /* total ever connected, for ID assignment */
    int current_connected;       /* currently active clients */
    int active;                  /* 1 if server is running, 0 if not */
    int max_fd;                  /* highest fd, needed for select() */
    fd_set all_fds;              /* master fd set for select() */
};


// Send a null-terminated string of length len to a client,
// appending \r\n. Returns 0 on success, 1 on error, 2 on disconnect.
int write_buf_to_client(struct client_sock *c, char *buf, int len);


//Remove *curr from the clients list. Updates *curr to point to
//the next node. Updates *clients if the head was removed.
//Returns 0 on success, 1 on failure.
int remove_client(struct client_sock **curr, struct client_sock **clients);


//Read available bytes from client into its buffer.
//Returns: -1 on error, 0 if complete message received, 1 if client closed, 2 if partial message.
int read_from_client(struct client_sock *curr);


// Assign an integer id to a newly connected client.
//Sends "clientN:" as a confirmation back to the client
//so it knows its own ID. Returns 0 on success, 1 on failure.
int assign_client_id(struct client_sock *curr, int id);


// Broadcast a message to all clients in the list.
//Disconnects any client that fails to receive.
//server: needed to update fd_set and current_connected on disconnect.
void broadcast(struct server_state *server, const char *msg, int len);

#endif
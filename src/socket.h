#ifndef _SOCKET_H_
#define _SOCKET_H_

#include <netinet/in.h>

#ifndef MAX_CONNECTIONS
    #define MAX_CONNECTIONS 12
#endif

#ifndef MAX_BACKLOG
    #define MAX_BACKLOG 5
#endif

#ifndef MAX_NAME
    #define MAX_NAME 10
#endif

#ifndef MAX_USER_MSG
    #define MAX_USER_MSG 128
#endif

#ifndef MAX_PROTO_MSG
    #define MAX_PROTO_MSG MAX_NAME+2+MAX_USER_MSG+2
#endif

#ifndef BUF_SIZE
    #define BUF_SIZE MAX_PROTO_MSG+1
#endif


struct listen_sock {
    struct sockaddr_in *addr;
    int sock_fd;
};

/* Takes runtime port number instead of hardcoded SERVER_PORT */
int setup_server_socket(struct listen_sock *s, int port);

int find_network_newline(const char *buf, int n);
int read_from_socket(int sock_fd, char *buf, int *inbuf);
int get_message(char **dst, char *src, int *inbuf);
int write_to_socket(int sock_fd, char *buf, int len);

#endif


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <errno.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <netinet/in.h>

#include "socket.h"

int setup_server_socket(struct listen_sock *s, int port) {

    if (!(s->addr = malloc(sizeof(struct sockaddr_in)))) {
        perror("malloc");
        return -1;
    }

    s->addr->sin_family = AF_INET;
    s->addr->sin_port = htons(port);   /* runtime port */

    memset(&(s->addr->sin_zero), 0, 8);
    
    s->addr->sin_addr.s_addr = INADDR_ANY;

    s->sock_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (s->sock_fd < 0) {
        perror("server socket");
        return -1;
    }

    int on = 1;
    if (setsockopt(s->sock_fd, SOL_SOCKET, SO_REUSEADDR,
                   (const char *)&on, sizeof(on)) < 0) {
        perror("setsockopt");
        return -1;
    }

    if (bind(s->sock_fd, (struct sockaddr *)s->addr,
             sizeof(*(s->addr))) < 0) {
        perror("server: bind");
        close(s->sock_fd);
        return -1;
    }

    if (listen(s->sock_fd, MAX_BACKLOG) < 0) {
        perror("server: listen");
        close(s->sock_fd);
        return -1;
    }

    return 0;
}

int find_network_newline(const char *buf, int inbuf) {
    for (int i=0; i<inbuf-1; i++) {
        if (buf[i] == '\r' && buf[i+1] == '\n') {
            return i + 2;
        }
    }
    return -1;
}

int read_from_socket(int sock_fd, char *buf, int *inbuf) {
    if (*inbuf >= BUF_SIZE - 1){
        return -1;
    }
    
    int num_read = read(sock_fd, buf + *inbuf, BUF_SIZE - *inbuf - 1);
    if (num_read < 0) return -1;
    if (num_read == 0) return 1;

    *inbuf += num_read;
    buf[*inbuf] = '\0';

    if (find_network_newline(buf, *inbuf) != -1){
        return 0;
    } 

    if (*inbuf == BUF_SIZE - 1) return -1;
    
    return 2;
}

int get_message(char **dst, char *src, int *inbuf) {
    int location = find_network_newline(src, *inbuf);
    if (location == -1) return 1;

    int msg_length = location - 2;
    *dst = malloc(msg_length + 1);
    if (*dst == NULL) return 1;

    memcpy(*dst, src, msg_length);
    (*dst)[msg_length] = '\0';

    int remaining = *inbuf - location;
    memmove(src, src + location, remaining);
    *inbuf = remaining;
    src[*inbuf] = '\0';

    return 0;
}

int write_to_socket(int sock_fd, char *buf, int len) {
    int sent = 0;
    while (sent < len) {
        int n = write(sock_fd, buf + sent, len - sent);
        if (n < 0) {
            if (errno == EINTR){
                continue;
            }
            if (errno == EPIPE || errno == ECONNRESET){
                return 2;
            }
            return 1;
        }
        if (n == 0){
            return 2;
        }
        sent += n;
    }

    return 0;
}
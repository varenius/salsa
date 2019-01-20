#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

#include "socket.h"

/**
 * reference count management for file descriptor.
 */
struct sockfd_ptr {
  int _fd;
  unsigned _count;
};

/**
 * Create a reference count manager for fd.
 * The socket associated with fd will be closed when there are no
 * active references to it.
 */
static int *
make_fd_ref(int fd)
{
  if (fd < 0) {
    return NULL;
  }
  struct sockfd_ptr *rc = (struct sockfd_ptr *) calloc(1, sizeof(struct sockfd_ptr));
  if (!rc) {
    return NULL;
  }
  rc->_fd = fd;
  rc->_count = 1;
  return (int *)rc;
}

/**
 * Increment reference count for file descriptor managed by fd_ref.
 */
static int *
increment_fd_ref(int *fd_ref)
{
  struct sockfd_ptr *rc = (struct sockfd_ptr *)fd_ref;
  switch(rc->_count++) {
  case 0:
    rc->_count = 0;
  }
  return fd_ref;
}

/**
 * Decrement reference count for file descriptor managed by fd_ref.
 */
static void
decrement_fd_ref(int *fd_ref)
{
  struct sockfd_ptr *rc = (struct sockfd_ptr *)fd_ref;
  switch(rc->_count--) {
  case 1:
    shutdown(rc->_fd, SHUT_RDWR);
    close(rc->_fd);
    rc->_fd = -1;
    free(rc);
    break;
  case 0:
    rc->_count = 0;
  }
}

/**
 * Data structure for socket connections.
 */
struct socket_t {
  int *sockfd;
  char host[16];
  uint16_t port;
};

/**
 * Initialize self and connect to host on port.
 */
static int
Socket_init(Socket *self,
	    char const *host,
	    uint16_t port)
{
  if (!self) {
    return 0;
  }
  self->sockfd = make_fd_ref(socket(AF_INET, SOCK_STREAM, 0));
  if (!self->sockfd) {
    return 0;
  }

  strcpy(self->host, host);
  self->port = port;

  struct sockaddr_in addr;
  addr.sin_family = AF_INET;
  addr.sin_port = htons(self->port);
  addr.sin_addr.s_addr = inet_addr(self->host);
  if (connect(*self->sockfd, (struct sockaddr *)&addr, sizeof(struct sockaddr_in)) < 0) {
    fprintf(stderr, "Error connecting to %s on port %d: %s\n", self->host, self->port, strerror(errno));
    decrement_fd_ref(self->sockfd);
    return 0;
  }
  
  return 1;
}

/**
 * Release all resources allocated in self.
 */
static void
Socket_destroy(Socket *self)
{
  if (!self) {
    return;
  }
  decrement_fd_ref(self->sockfd);
  self->sockfd = NULL;
}

Socket *
Socket_new(char const *host,
	   uint16_t port)
{
  Socket *sock = (Socket *) calloc(1, sizeof(Socket));
  if (!Socket_init(sock, host, port)) {
    free(sock);
    sock = NULL;
  }
  return sock;
}

void
Socket_delete(Socket *self)
{
  Socket_destroy(self);
  free(self);
}

Socket *
Socket_copy(Socket *self)
{
  Socket *cp = (Socket *) calloc(1, sizeof(Socket));
  if (!cp) {
    return NULL;
  }
  *cp = *self;
  cp->sockfd = increment_fd_ref(self->sockfd);
  return cp;
}

int
Socket_recv(Socket *self,
	    char *bfr,
	    size_t len)
{
  switch(recv(*self->sockfd, bfr, len, 0)) {
  case -1:
    fprintf(stderr, "Error reading from socket stream: %s\n", strerror(errno));
  case 0:
    return 0;
  default:
    return 1;
  }
}

int
Socket_send(Socket *self,
	    char const *bfr,
	    size_t len)
{
  if (send(*self->sockfd, bfr, len, 0) < 0) {
    fprintf(stderr, "Error writing to socket stream: %s\n", strerror(errno));
    return 0;
  }
  return 1;
}

char const *
Socket_host(Socket *self)
{
  return self->host;
}

uint16_t
Socket_port(Socket *self)
{
  return self->port;
}

/**
 * Data structure for server socket connections.
 */
struct server_socket_t {
  int *sockfd;
  socklen_t addrlen;
  struct sockaddr_in addr;
  char host[16];
  uint16_t port;

  int backlog;
};

/**
 * Initialize self with backlog connection reattempts and bind it to port.
 */
static int
ServerSocket_init(ServerSocket *self, uint16_t port, int backlog)
{
  if (!self) {
    return 0;
  }

  strcpy(self->host, "127.0.0.1");
  self->port = port;
  self->backlog = backlog;
  self->addrlen = sizeof(struct sockaddr_in);
  
  self->sockfd = make_fd_ref(socket(AF_INET, SOCK_STREAM, 0));
  if (!self->sockfd) {
    fprintf(stderr, "Error creating socket: %s\n", strerror(errno));
    return 0;
  }

  int opt = 1;
  if (setsockopt(*self->sockfd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(int))) {
    fprintf(stderr, "Error setting socket options: %s\n", strerror(errno));
    decrement_fd_ref(self->sockfd);
    return 0;
  }

  self->addr.sin_family = AF_INET;
  self->addr.sin_port = htons(self->port);
  if(inet_pton(AF_INET, self->host, &self->addr.sin_addr) <= 0) {
    fprintf(stderr, "Error converting IPv4 address '%s' to binary form: %s\n",
	    self->host, strerror(errno));
    decrement_fd_ref(self->sockfd);
    return 0;
  }
  
  if (bind(*self->sockfd, (struct sockaddr *)&self->addr, sizeof(struct sockaddr_in)) < 0) {
    fprintf(stderr, "Error binding socket to address: %s\n", strerror(errno));
    decrement_fd_ref(self->sockfd);
    return 0;
  }

  return 1;
}

/**
 * Release all resources allocated in self.
 */
static void
ServerSocket_destroy(ServerSocket *self)
{
  if (!self) {
    return;
  }
  decrement_fd_ref(self->sockfd);
}

ServerSocket *
ServerSocket_new(uint16_t port,
		 int backlog)
{
  ServerSocket *ssock = (ServerSocket *) calloc(1, sizeof(ServerSocket));
  if (!ServerSocket_init(ssock, port, backlog)) {
    free(ssock);
    ssock = NULL;
  }
  return ssock;
}

void
ServerSocket_delete(ServerSocket *self)
{
  ServerSocket_destroy(self);
  free(self);
}

ServerSocket *
ServerSocket_copy(ServerSocket *self)
{
  ServerSocket *cp = (ServerSocket *) calloc(1, sizeof(Socket));
  if (!cp) {
    return NULL;
  }
  *cp = *self;
  cp->sockfd = increment_fd_ref(self->sockfd);
  return cp;
}

int
ServerSocket_listen(ServerSocket *self)
{
  if (listen(*self->sockfd, self->backlog) < 0) {
    fprintf(stderr, "Error listening on socket: %s\n", strerror(errno));
    return 0;
  }
  return 1;
}

Socket *
ServerSocket_accept(ServerSocket *self)
{
  int *sock = make_fd_ref(accept(*self->sockfd, (struct sockaddr *)&self->addr, &self->addrlen));
  if (!sock) {
    fprintf(stderr, "Error accepting new connection: %s\n", strerror(errno));
    return NULL;
  }
  
  Socket *nc = (Socket *) calloc(1, sizeof(Socket));
  if (!nc) {
    decrement_fd_ref(sock);
    return NULL;
  }
  
  nc->sockfd = increment_fd_ref(sock);
  strcpy(nc->host, inet_ntoa(self->addr.sin_addr));
  nc->port = ntohs(self->addr.sin_port);

  decrement_fd_ref(sock);
  return nc;
}

char const *
ServerSocket_host(ServerSocket *self)
{
  return self->host;
}

uint16_t
ServerSocket_port(ServerSocket *self)
{
  return self->port;
}

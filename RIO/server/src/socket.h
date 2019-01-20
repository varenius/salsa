#ifndef SOCKET_H_INCLUDED
#define SOCKET_H_INCLUDED

#include <stdint.h>
#include <stdlib.h>

typedef struct socket_t Socket;

/**
 * Create a Socket object and connect to host on port.
 */
Socket *
Socket_new(char const *host, uint16_t port);

/**
 * Deallocate all resources allocated in the Socket object and destroy it.
 */
void
Socket_delete(Socket *self);

/**
 * Create a shallow copy of the socket object (the copy uses the same
 * underlying file descriptor).
 */
Socket *
Socket_copy(Socket *self);

/**
 * Read up to len bytes to bfr from the socket stream.
 */
int
Socket_recv(Socket *self, char *bfr, size_t len);

/**
 * Write len bytes from bfr to the socket stream.
 */
int
Socket_send(Socket *self, char const *bfr, size_t len);

/**
 * Retrieve the host address of the socket connection.
 */
char const *
Socket_host(Socket *self);

/**
 * Retrieve the port of the socket connection.
 */
uint16_t
Socket_port(Socket *self);


typedef struct server_socket_t ServerSocket;

/**
 * Create a ServerSocket object and listen on port with up to backlog connection reattempts.
 */
ServerSocket *
ServerSocket_new(uint16_t port, int backlog);

/**
 * Deallocate all resources allocated in the ServerSocket object and destroy it.
 */
void
ServerSocket_delete(ServerSocket *self);

/**
 * Create a shallow copy of the server socket object (the copy uses the same
 * underlying file descriptor).
 */
ServerSocket *
ServerSocket_copy(ServerSocket *self);

/**
 * Listen for connection attempts to the port that the server socket is bound to.
 */
int
ServerSocket_listen(ServerSocket *self);

/**
 * Wait for a connection attempt.
 */
Socket *
ServerSocket_accept(ServerSocket *self);

/**
 * Retrieve the host address of the socket connection (i.e. localhost).
 */
char const *
ServerSocket_host(ServerSocket *self);

/**
 * Retrieve the port that the socket is bound to.
 */
uint16_t
ServerSocket_port(ServerSocket *self);

#endif /* SOCKET_H_INCLUDED */

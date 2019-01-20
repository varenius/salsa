#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <stdint.h>
#include <ctype.h>
#include <stdbool.h>

#include <pthread.h>
#include <signal.h>

#include "hashtable.h"
#include "rio.h"
#include "socket.h"
#include "util.h"

/**
 * Key-value pairs for getter functions.
 */
struct getter_pair {
  char const *key;
  val_getter *val;
};

/**
 * List of key-value pairs for reading selected RIO variables.
 */
static struct getter_pair getter_entries[] = {
  { "minaz",    get_minaz },
  { "minel",    get_minel },
  { "maxaz",    get_maxaz },
  { "maxel",    get_maxel },
  { "az_dpch",  get_az_dpch },
  { "el_dpch",  get_el_dpch },
  { "cls_az",   get_cls_az },
  { "cls_el",   get_cls_el },
  { "vcls_az",  get_vcls_az },
  { "vcls_el",  get_vcls_el },
  { "close_az", get_close_az },
  { "close_el", get_close_el },
  { "samples",  get_samples },
  { "c_az",     get_c_az },
  { "c_el",     get_c_el },
  { "t_az",     get_t_az },
  { "t_el",     get_t_el },
  { "knowpos",  get_knowpos },
  { "stuck",    get_stuck },
  { "tol",      get_tol },
  { "stks",     get_stks },
  { NULL,       NULL }
};

/**
 * Key-value pairs for setter functions.
 */
struct setter_pair {
  char const *key;
  val_setter *val;
};

/**
 * List of key-value pairs for writing to selected RIO variables.
 */
static struct setter_pair setter_entries[] = {
  { "minaz",    set_minaz },
  { "minel",    set_minel },
  { "maxaz",    set_maxaz },
  { "maxel",    set_maxel },
  { "az_dpch",  set_az_dpch },
  { "el_dpch",  set_el_dpch },
  { "cls_az",   set_cls_az },
  { "cls_el",   set_cls_el },
  { "vcls_az",  set_vcls_az },
  { "vcls_el",  set_vcls_el },
  { "close_az", set_close_az },
  { "close_el", set_close_el },
  { "samples",  set_samples },
  { "t_az",     set_t_az },
  { "t_el",     set_t_el },
  { "knowpos",  set_knowpos },
  { "stuck",    set_stuck },
  { "tol",      set_tol },
  { "stks",     set_stks },
  { NULL,       NULL }
};

/**
 * Server for managing a single connection to the virtual RIO
 */
typedef struct world_server_t {
  RIO *_rio;
  GetterMap *getters;
  SetterMap *setters;
  Socket *sock;
  bool serving;
  pthread_t thread;
} WorldServer;

/**
 * Initialize the server.
 */
static int
WorldServer_init(WorldServer *self,
		 RIO *rio_,
		 GetterMap *getters,
		 SetterMap *setters,
		 Socket *sock)
{
  if (!self) {
    return 0;
  }
  self->_rio = rio_;
  self->getters = getters;
  self->setters = setters;
  self->sock = Socket_copy(sock);
  self->serving = false;
  return 1;
}

/**
 * Destroy the server.
 */
static void
WorldServer_destroy(WorldServer *self)
{
  if (!self) {
    return;
  }
  if (self->sock) {
    printf("Terminating service for %s on port %d\n", Socket_host(self->sock), Socket_port(self->sock));
  }
  self->serving = false;
  Socket_delete(self->sock);
  self->sock = NULL;
  pthread_join(self->thread, NULL);
}

/**
 * Whether or not the server is serving its client.
 */
static bool
WorldServer_serving(WorldServer *self)
{
  return self->serving;
}

/**
 * Write the value of the (virtual) RIO's variable vn into val.
 */
static int
WorldServer_get_var(WorldServer *self,
		    char const *vn,
		    double *val)
{
  val_getter *fn = GetterMap_get(self->getters, vn);
  if (!fn) {
    return 0;
  }
  *val = fn(self->_rio);
  return 1;
}

/**
 * Write val into the (virtual) RIO's variable vn.
 */
static int
WorldServer_set_var(WorldServer *self,
		    char const *vn,
		    double val)
{
  val_setter *fn = SetterMap_get(self->setters, vn);
  if (!fn) {
    return 0;
  }
  fn(self->_rio, val);
  return 1;
}

/**
 * Buffer size that is used when serving the client.
 */
#define WSR_BSIZE 64

/**
 * Parse, process and respond to the clients request.
 * It is limited to what is used in the SALSA control code.
 */
static WorldServer *
WorldServer_run(WorldServer *self)
{
  char bfr_out[WSR_BSIZE+1], bfr_in[WSR_BSIZE+1];
  while (self->serving) {
    memset(bfr_in, 0, sizeof(bfr_in));
    if (!Socket_recv(self->sock, bfr_in, WSR_BSIZE)) {
      self->serving = false;
      break;
    }

    char *msg = strip(bfr_in);
    if (strncmp(msg, "MG", 2) == 0) {
      double val = 0;
      if (WorldServer_get_var(self, lstrip(msg+2), &val)) {
	sprintf(bfr_out, " %.4f\r\n:", val);
      } else {
	sprintf(bfr_out, "?");
      }
    } else if (strstr(msg, "=")) {
      char *eq = strstr(msg, "=");
      *eq = '\0'; /* create an artificial split */
      char *lhs = rstrip(msg);
      char *rhs = lstrip(eq + 1);
      char *end = rhs;
      int val = strtol(rhs, &end, 10);
      if (!*end && WorldServer_set_var(self, lhs, val)) {
	sprintf(bfr_out, ":");
      } else {
	sprintf(bfr_out, "?");
      }
    } else if (strncmp(msg, "RS", 2) == 0) {
      if (RIO_hard_reset(self->_rio)) {
	sprintf(bfr_out, "\r\n:");
      } else {
	sprintf(bfr_out, "?");
      }
    } else if (strncmp(msg, "XQ", 2) == 0) {
      msg = lstrip(msg+2);
      if (strncmp(msg, "#INIT", 5) == 0) {
	RIO_start_move_loop(self->_rio);
	sprintf(bfr_out, ":");
      } else {
	sprintf(bfr_out, "?");
      }
    } else if (strncmp(msg, "HX", 2) == 0) {
      msg = lstrip(msg+2);
      if (strncmp(msg, "0", 1) == 0) {
	RIO_stop_move_loop(self->_rio);
      }
      sprintf(bfr_out, ":");
    } else if (strncmp(msg, "CB", 2) == 0) {
      msg = lstrip(msg+2);
      if (strncmp(msg, "8", 1) == 0) {
	RIO_clear_lna(self->_rio);
      } else if (strncmp(msg, "9", 1) == 0) {
	RIO_clear_diode(self->_rio);
      }
      sprintf(bfr_out, ":");
    } else if (strncmp(msg, "SB", 2) == 0) {
      msg = lstrip(msg+2);
      if (strncmp(msg, "8", 1) == 0) {
	RIO_set_lna(self->_rio);
      } else if (strncmp(msg, "9", 1) == 0) {
	RIO_set_diode(self->_rio);
      }
      sprintf(bfr_out, ":");
    } else if (*msg == '\0') {
      sprintf(bfr_out, ":");
    } else {
      sprintf(bfr_out, "?");
    }
    Socket_send(self->sock, bfr_out, strlen(bfr_out));
  }
  return self;
}

/**
 * Start serving the client.
 */
int WorldServer_serve(WorldServer *self)
{
  printf("Commencing service for %s on port %d\n", Socket_host(self->sock), Socket_port(self->sock));
  self->serving = true;
  if (pthread_create(&self->thread, NULL, (void*(*)(void*))WorldServer_run, self)) {
    fprintf(stderr, "Error starting WorldServer: %s\n", strerror(errno));
    self->serving = false;
    return 0;
  }
  return 1;
}

/**
 * Server for handling connections to the server.
 * Once a connection have been made it is passed on to a handler that will
 * continue to server the client's requests.
 */
typedef struct login_server_t {
  ServerSocket *ssock;

  RIO *_rio;
  GetterMap *getters;
  SetterMap *setters;
  int accepting;
  size_t max_connections;
  WorldServer *connections;
  WorldServer *begin;
  WorldServer *end;
} LoginServer;

/**
 * Initialize the server to listen on port and allow up to max_connections
 * simultaneous connections.
 */
static int
LoginServer_init(LoginServer *self, RIO *rio_, uint16_t port, int backlog, size_t max_connections)
{
  self->ssock = ServerSocket_new(port, backlog);
  if (!self->ssock) {
    return 0;
  }

  self->connections = (WorldServer *) calloc(max_connections+1, sizeof(WorldServer));
  if (!self->connections) {
    ServerSocket_delete(self->ssock);
    self->ssock = NULL;
    self->begin = self->end = NULL;
    return 0;
  }

  
  self->getters = GetterMap_new();
  self->setters = SetterMap_new();
  if (!self->getters || !self->setters) {
    ServerSocket_delete(self->ssock);
    GetterMap_delete(self->getters);
    SetterMap_delete(self->setters);
    return 0;
  }
  
  for (struct getter_pair *p = getter_entries; p->key; ++p) {
    GetterMap_put(self->getters, p->key, p->val);
  }
  for (struct setter_pair *p = setter_entries; p->key; ++p) {
    SetterMap_put(self->setters, p->key, p->val);
  }

  self->_rio = rio_;
  self->accepting = 0;
  self->max_connections = max_connections;
  self->begin = self->connections;
  self->end = self->begin + self->max_connections;
  return 1;
}

/**
 * Terminate the server and all active handlers.
 */
void LoginServer_destroy(LoginServer *self)
{
  if (!self) {
    return;
  }
  if (self->ssock) {
    printf("Terminating login service for %s on port %d\n",
	   ServerSocket_host(self->ssock), ServerSocket_port(self->ssock));
  }
  self->accepting = 0;
  ServerSocket_delete(self->ssock);
  self->ssock = NULL;
  
  for (WorldServer *slot = self->begin; slot != self->end; ++slot) {
    WorldServer_destroy(slot);
  }
  free(self->connections);
  self->connections = NULL;
  self->max_connections = 0;
  
  SetterMap_delete(self->setters);
  GetterMap_delete(self->getters);
}

/**
 * Find the first available client handler.
 */
WorldServer *LoginServer_first_available(LoginServer *self)
{
  for (WorldServer *slot = self->begin; slot != self->end; ++slot) {
    if (!WorldServer_serving(slot)) {
      WorldServer_destroy(slot);
      return slot;
    }
  }
  return NULL;
}

/**
 * Start the server.
 */
int LoginServer_serve(LoginServer *self)
{
  printf("Commencing login service for %s on port %d\n",
	 ServerSocket_host(self->ssock), ServerSocket_port(self->ssock));

  if (!ServerSocket_listen(self->ssock)) {
    return 0;
  }
  self->accepting = 1;

  while (self->accepting) {
    Socket *nc = ServerSocket_accept(self->ssock);
    if (!nc) {
      fprintf(stderr, "Error accepting new connection: %s\n", strerror(errno));
      continue;
    }
    
    WorldServer *handler = LoginServer_first_available(self);
    if (handler && WorldServer_init(handler, self->_rio, self->getters, self->setters, nc)) {
      WorldServer_serve(handler);
    } else {
      fprintf(stderr, "Error finding handler for new connection\n");
    }
    Socket_delete(nc);
  }
  return 1;
}


/**
 * Ensures that the server is terminated on abnormal exit.
 */
static struct sigaction sa_sigint, sa_sigabrt, sa_sigterm;

/**
 * Initialize signal handlers.
 */
static int
init_sigaction(struct sigaction *sa,
	       int signum,
	       void (*handler)(int))
{
  sigemptyset(&sa->sa_mask);
  sa->sa_flags = 0;
  sa->sa_handler = handler;
  return sigaction(signum, sa, NULL);
}

/**
 * The RIO server.
 */
static LoginServer server;

/**
 * The virtual RIO.
 */
static RIO *rio;

/**
 * Destroy objects if the program is terminated by the operating environment.
 */
static void
exit_signal_handler(int sig)
{
  signal(sig, SIG_IGN);
  
  LoginServer_destroy(&server);
  RIO_delete(rio);
  
  signal(sig, SIG_DFL);
  raise(sig);
}

/**
 * Setup signal handlers.
 */
static void
setup_signal_handling(void)
{
  if (init_sigaction(&sa_sigint, SIGINT, exit_signal_handler) < 0) {
    fprintf(stderr, "Error initializing SIGINT handler: %s\n", strerror(errno));
    exit(SIGINT);
  }
  if (init_sigaction(&sa_sigabrt, SIGABRT, exit_signal_handler) < 0) {
    fprintf(stderr, "Error initializing SIGABRT handler: %s\n", strerror(errno));
    exit(SIGABRT);
  }
  if (init_sigaction(&sa_sigterm, SIGTERM, exit_signal_handler) < 0) {
    fprintf(stderr, "Error initializing SIGTERM handler: %s\n", strerror(errno));
    exit(SIGTERM);
  }
}

int
main(int argc,
     char *argv[])
{
  setup_signal_handling();

  if (argc < 4) {
    fprintf(stderr, "Usage: %s <TARGET> <RIO-IP> <RIO-PORT>\n", argv[0]);
  } else {
    if (strncmp("VALE", argv[1], 4) == 0) {
      rio = RIO_new(VALE, argv[2], atoi(argv[3]));
    } else if (strncmp("BRAGE", argv[1], 5) == 0) {
      rio = RIO_new(BRAGE, argv[2], atoi(argv[3]));
    } else {
      fprintf(stderr, "target '%s' is not valid (specify VALE/BRAGE)", argv[1]);
    }
  }
  if (!rio) {
    return EXIT_FAILURE;
  }
  
  if (!LoginServer_init(&server, rio, 55555, 3, 3)) {
    RIO_delete(rio);
    return EXIT_FAILURE;
  }
  
  LoginServer_serve(&server);
  
  LoginServer_destroy(&server);
  RIO_delete(rio);
  
  return EXIT_SUCCESS;
}

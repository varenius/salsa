#include <stdlib.h>
#include <stdbool.h>
#include <pthread.h>
#include <time.h>
#include <string.h>
#include <errno.h>
#include <stdio.h>
#include <math.h>

#include "rio.h"
#include "socket.h"

/**
 * Program can be used without a physical RIO unit by defining
 * this as 0. Doing so will leave the response buffer empty.
 */
#define USING_PHYSICAL_RIO 1

/**
 * Buffer size to be used for the RIO connection. Messages are
 * typically short (< 16 bytes).
 */
#define RC_BUFSIZE 0x100

typedef void*(*pthread_routine)(void*);

/**
 * returns min <= v <= max;
 */
static int
clip(int v,
     int min,
     int max)
{
  return v < min ? min : v > max ? max : v;
}

/**
 * returns the square of x.
 */
static double
sqr(double x)
{
  return x*x;
}

/**
 * Retrieves system time in seconds (nanosecond resolution).
 */
static double
get_time(void)
{
  struct timespec t;
  clock_gettime(CLOCK_MONOTONIC, &t);
  return t.tv_sec + t.tv_nsec / 1e9;
}

/**
 * halts execution on the calling thread for t_s seconds (nanosecond resolution).
 */
static void
sleep_s(double t_s)
{
  if (t_s > 0) {
    struct timespec t = {(time_t)t_s, (long)((t_s-(time_t)t_s)*1000000000)};
    clock_nanosleep(CLOCK_MONOTONIC, 0, &t, NULL);
  }
}

/**
 * halts execution on the calling thread for t_ms milliseconds.
 */
static void
sleep_ms(uint64_t t_ms)
{
  if (t_ms > 0) {
    struct timespec t = {(time_t)(t_ms/1000), (long)((t_ms%1000)*1000000)};
    clock_nanosleep(CLOCK_MONOTONIC, 0, &t, NULL);
  }
}

/**
 * Request/response buffers for communicating with the physical RIO
 */
struct io_buffer {
  char request[RC_BUFSIZE+1];
  char response[RC_BUFSIZE+1];
};

/**
 * The connection to the physical RIO unit.
 */
typedef struct connection_t {
  Socket *sock;
  pthread_mutex_t mutx;
} Connection;

/**
 * Initialize self with a connection to host:port.
 */
static int
Connection_init(Connection *self,
		char const *host,
		uint16_t port)
{
  if (!self) {
    return 0;
  }
#if USING_PHYSICAL_RIO
  self->sock = Socket_new(host, port);
  if (!self->sock) {
    return 0;
  }
#endif
  pthread_mutex_init(&self->mutx, NULL);
  return 1;
}

/**
 * Releases all resources allocated in self.
 */
static void
Connection_destroy(Connection *self)
{
  if (!self) {
    return;
  }
  pthread_mutex_destroy(&self->mutx);
#if USING_PHYSICAL_RIO
  Socket_delete(self->sock);
#endif
}

/**
 * Closes the connection and opens a new connection to the physical RIO
 */
static int
Connection_reset(Connection *self)
{
#if USING_PHYSICAL_RIO
  pthread_mutex_lock(&self->mutx);
  uint16_t port = Socket_port(self->sock);
  char *host = strdup(Socket_host(self->sock));
  if (!host) {
    fprintf(stderr, "Error duplicating socket host string: %s\n", strerror(errno));
    return 0;
  }
  Socket_delete(self->sock);
  sleep_ms(1);			/* wait for physical RIO to close connection */
  self->sock = Socket_new(host, port);
  free(host);
  int status = self->sock != NULL;
  pthread_mutex_unlock(&self->mutx);
  return status;
#endif
  return 1;
}

/**
 * Sends the contents of the supplied request buffer to the
 * physical RIO and writes the response in the supplied
 * response buffer.
 * Node: thread safety needs to be provided by the caller.
 */
static int
Connection_send_and_receive(Connection *self,
			    struct io_buffer *buf)
{
#if USING_PHYSICAL_RIO
  pthread_mutex_lock(&self->mutx);
  int status = Socket_send(self->sock, buf->request, strlen(buf->request)) &&
    Socket_recv(self->sock, buf->response, RC_BUFSIZE);
  pthread_mutex_unlock(&self->mutx);
  return status;
#else
  return 1;
#endif
}

/**
 * Print an error message if strtod failed.
 */
static void
print_strtod_error(char const *response,
		   char const *var_name)
{
  fprintf(stderr, "Error converting value of '%s' from RIO to float (response was '", var_name);
  for (char const *c = response; *c; ++c) {
    switch(*c) {
    case '\r': fprintf(stderr, "\\r"); break;
    case '\n': fprintf(stderr, "\\n"); break;
    default: fprintf(stderr, "%c", *c); break;
    }
  }
  fprintf(stderr, "').\n");
}

/**
 * Send a command (i.e. no response expected) to the physical RIO.
 * Provides thread safety on the internal request and response
 * buffers as well as sending and receiving messages.
 */
static int
send_command(Connection *self,
	     char const *cmd)
{
  struct io_buffer buf;
  int bfr_status = snprintf(buf.request, RC_BUFSIZE, "%s\r", cmd);
  if (bfr_status < 0) {
    fprintf(stderr, "output error in send_command. request was not sent\n");
    return 0;
  }
  if (bfr_status >= RC_BUFSIZE) {
    fprintf(stderr, "buffer overflow in send_command. request was not sent\n");
    return 0;
  }
  return Connection_send_and_receive(self, &buf);
}

/**
 * Requests a float value from the physical RIO and returns it.
 * Provides thread safety on the internal request and response
 * buffers as well as sending and receiving messages.
 */
static double
get_float(Connection *self,
	  char const *var_name)
{
  struct io_buffer buf;
  int bfr_status = snprintf(buf.request, RC_BUFSIZE, "MG %s\r", var_name);
  if (bfr_status < 0) {
    fprintf(stderr, "output error in send_command. request was not sent\n");
    return 0;
  }
  if (bfr_status >= RC_BUFSIZE) {
    fprintf(stderr, "buffer overflow in send_command. request was not sent\n");
    return 0;
  }
  if (!Connection_send_and_receive(self, &buf)) {
    return 0;
  }

  /* response begins with ' ' and ends with '\r\n:' */
  char *begin = buf.response+1, *end = NULL;
  double val = strtod(begin, &end);
#if USING_PHYSICAL_RIO
  if (end == begin) {
    print_strtod_error(buf.response, var_name);
  }
#endif
  return val;
}

/**
 * Requests an integer value from the physical RIO and returns it.
 * Provides thread safety on the internal request and response
 * buffers as well as sending and receiving messages.
 */
static int
get_int(Connection *self,
	char const *var_name)
{
  return (int) get_float(self, var_name);
}

/**
 * Possible states for the azimuth and elevation relative encoder.
 */
enum detector_state {
  ds_undefined = -1,
  ds_low = 0,
  ds_high = 1
};

/**
 * Axis-specific data and functions. This struct provides a common
 * inteface for azimuth and elevation so that the same functions
 * can be used for both axes.
 */
struct motor_axis {
  int min, max;
  volatile int current;
  int target, requested;
  int close, very_close;
  double deg_per_cog_hole;
  enum detector_state detector_state;

  int  (*get_detector_state)(RIO *self);
  void (*start_motor)(RIO *self);
  void (*stop_motor)(RIO *self);
  void (*set_motor_ccw_mode)(RIO *self);
  void (*clear_motor_ccw_mode)(RIO *self);
  int  (*motor_ccw_mode)(RIO *self);
  void (*set_detector_status_led)(RIO *self);
  void (*clear_detector_status_led)(RIO *self);
  void (*update_detector_status_led)(RIO *self);
};

struct motor_duty_cycle {
  int min, max;
  double scale;
};

/**
 * The virtual RIO unit.
 */
struct RIO_t {
  Connection rcon;
  bool run_monitor_position, run_move_loop;
  pthread_t monitor_position_thrd, move_loop_thrd;

  int stuck_tol;
  int pos_samples, stuck_samples, stop_samples;

  enum system_host target;
  struct motor_axis az, el;
  struct motor_duty_cycle mds_data;
  bool knowpos;
  bool stuck;
};


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                            Physical RIO interface                             *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * Requests the relative encoder for elevation.
 */
static int
detector_el_state(RIO *self)
{
  return get_int(&self->rcon, "@IN[0]");
}

/**
 * Requests the relative encoder for azimuth.
 */
static int
detector_az_state(RIO *self)
{
  return get_int(&self->rcon, "@IN[1]");
}

/**
 * Starts the elevation motor.
 */
static void
motor_start_el(RIO *self)
{
  send_command(&self->rcon, "SB0");
}

/**
 * Stops the elevation motor.
 */
static void
motor_stop_el(RIO *self)
{
  send_command(&self->rcon, "CB0");
}

/**
 * Sets the CCW mode (position decreases when motor runs)
 * for the elevation motor.
 */
static void
motor_set_el_ccw_mode(RIO *self)
{
  send_command(&self->rcon, "SB1");
}

/**
 * Clears the CCW mode (position increases when motor runs)
 * for the elevation motor.
 */
static void
motor_clear_el_ccw_mode(RIO *self)
{
  send_command(&self->rcon, "CB1");
}

/**
 * Requests the CCW mode status for the elevation motor.
 */
static int
motor_el_ccw_mode(RIO *self)
{
  return get_int(&self->rcon, "@OUT[1]");
}

/**
 * Starts the azimuth motor.
 */
static void
motor_start_az(RIO *self)
{
  send_command(&self->rcon, "SB2");
}

/**
 * Stops the azimuth motor.
 */
static void
motor_stop_az(RIO *self)
{
  send_command(&self->rcon, "CB2");
}

/**
 * Sets the CCW mode (position decreases when motor runs)
 * for the azimuth motor.
 */
static void
motor_set_az_ccw_mode(RIO *self)
{
  send_command(&self->rcon, "SB3");
}

/**
 * Clears the CCW mode (position increases when motor runs)
 * for the azimuth motor.
 */
static void
motor_clear_az_ccw_mode(RIO *self)
{
  send_command(&self->rcon, "CB3");
}

/**
 * Requests the CCW mode status for the azimuth motor.
 */
static int
motor_az_ccw_mode(RIO *self)
{
  return get_int(&self->rcon, "@OUT[3]");
}

/**
 * Turns on the elevation position status LED that is visible
 * from the control room.
 */
static void
display_set_el_led(RIO *self)
{
  send_command(&self->rcon, "SB4");
}

/**
 * Turns off the elevation position status LED that is visible
 * from the control room.
 */
static void
display_clear_el_led(RIO *self)
{
  send_command(&self->rcon, "CB4");
}

/**
 * Updates the elevation position status LED that is visible
 * from the control room so that it reflects the state of the
 * relative encoder for elevation.
 */
static void
update_el_led(RIO *self)
{
  switch (self->el.detector_state) {
  case ds_undefined:
    break;
  case ds_low:
    display_clear_el_led(self);
    break;
  case ds_high:
    display_set_el_led(self);
    break;
  }
}

/**
 * Turns on the azimuth position status LED that is visible
 * from the control room.
 */
static void
display_set_az_led(RIO *self)
{
  send_command(&self->rcon, "SB5");
}

/**
 * Turns off the azimuth position status LED that is visible
 * from the control room.
 */
static void
display_clear_az_led(RIO *self)
{
  send_command(&self->rcon, "CB5");
}

/**
 * Updates the azimuth position status LED that is visible
 * from the control room so that it reflects the state of the
 * relative encoder for azimuth.
 */
static void
update_az_led(RIO *self)
{
  switch (self->az.detector_state) {
  case ds_undefined:
    break;
  case ds_low:
    display_clear_az_led(self);
    break;
  case ds_high:
    display_set_az_led(self);
    break;
  }
}

/**
 * Turns on the LNAs that amplifies the signal from the antenna horn.
 */
static void
dish_set_lna(RIO *self)
{
  send_command(&self->rcon, "SB8");
}

/**
 * Turns off the LNAs that amplifies the signal from the antenna horn.
 */
static void
dish_clear_lna(RIO *self)
{
  send_command(&self->rcon, "CB8");
}

/**
 * Turns on the noise diode that is located on the telescope dish.
 */
static void
dish_set_diode(RIO *self)
{
  send_command(&self->rcon, "SB9");
}

/**
 * Turns off the noise diode that is located on the telescope dish.
 */
static void
dish_clear_diode(RIO *self)
{
  send_command(&self->rcon, "CB9");
}

/**
 * Resets the physical RIO to a power-on state.
 */
static void
RIO_to_power_on_state(RIO *self)
{
  send_command(&self->rcon, "RS");
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                 Virtual RIO                                   *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

static void RIO_stop_monitoring_position(RIO *self);
static RIO *RIO_monitor_position(RIO *self);
static RIO *RIO_move_loop(RIO *self);

RIO *
RIO_new(enum system_host target,
	char const *host,
	uint16_t port)
{
  RIO *self = (RIO *) calloc(1, sizeof(RIO));
  if (!self) {
    return NULL;
  }

  if (!Connection_init(&self->rcon, host, port)) {
    free(self);
    return NULL;
  }

  self->target = target;
  
  /* axis function pointers */
  self->az.get_detector_state = detector_az_state;
  self->el.get_detector_state = detector_el_state;
  self->az.start_motor = motor_start_az;
  self->el.start_motor = motor_start_el;
  self->az.stop_motor = motor_stop_az;
  self->el.stop_motor = motor_stop_el;
  self->az.set_motor_ccw_mode = motor_set_az_ccw_mode;
  self->el.set_motor_ccw_mode = motor_set_el_ccw_mode;
  self->az.clear_motor_ccw_mode = motor_clear_az_ccw_mode;
  self->el.clear_motor_ccw_mode = motor_clear_el_ccw_mode;
  self->az.motor_ccw_mode = motor_az_ccw_mode;
  self->el.motor_ccw_mode = motor_el_ccw_mode;
  self->az.set_detector_status_led = display_set_az_led;
  self->el.set_detector_status_led = display_set_el_led;
  self->az.clear_detector_status_led = display_clear_az_led;
  self->el.clear_detector_status_led = display_clear_el_led;
  self->az.update_detector_status_led = update_az_led;
  self->el.update_detector_status_led = update_el_led;

  RIO_hard_reset(self);
  return self;
}

void
RIO_delete(RIO *self)
{
  if (!self) {
    return;
  }
  RIO_stop_monitoring_position(self);
  RIO_stop_move_loop(self);
  self->az.stop_motor(self);
  self->el.stop_motor(self);
  self->az.clear_motor_ccw_mode(self);
  self->el.clear_motor_ccw_mode(self);
  self->az.clear_detector_status_led(self);
  self->el.clear_detector_status_led(self);
  dish_clear_lna(self);
  dish_clear_diode(self);

  Connection_destroy(&self->rcon);

  free(self);
}

/**
 * Stop the thread that monitors the position of the telescope.
 */
static void
RIO_stop_monitoring_position(RIO *self)
{
  if (self->run_monitor_position) {
    self->run_monitor_position = false;
    pthread_join(self->monitor_position_thrd, NULL);
  }
}

/**
 * Start the thread that monitors the position of the telescope.
 */
static void
RIO_start_monitoring_position(RIO *self)
{
  RIO_stop_monitoring_position(self);
  self->run_monitor_position = true;
  pthread_create(&self->monitor_position_thrd, NULL, (pthread_routine) RIO_monitor_position, self);
}

void
RIO_stop_move_loop(RIO *self)
{
  if (self->run_move_loop) {
    self->run_move_loop = false;
    pthread_join(self->move_loop_thrd, NULL);
  }
}

void
RIO_start_move_loop(RIO *self)
{
  RIO_stop_move_loop(self);
  self->run_move_loop = true;
  pthread_create(&self->move_loop_thrd, NULL, (pthread_routine) RIO_move_loop, self);
}

int
RIO_hard_reset(RIO *self)
{
  RIO_stop_move_loop(self);
  RIO_stop_monitoring_position(self);
  if (!Connection_reset(&self->rcon)) {
    return 0;
  }
  RIO_to_power_on_state(self);

  self->knowpos = false; /* =false move-loop or position monitoring not running, =true: OK */
  self->stuck = false;	 /* =false: OK, =true stuck */
  self->stuck_tol = 0; /* tolerance for current-target cog in stuck detection */
  self->pos_samples = 5; /* number of samples to average in when monitoring position. */
  self->stuck_samples = 29;	/* samples for stuck detection */
  self->stop_samples = 7; /* samples for stopping motor befor changing direction */

  /* Min and max positions */
  self->az.min = self->el.min = 20;
  switch(self->target) {
  case VALE:
    self->az.max = 2644;
    self->el.max = 1422;
    break;
  case BRAGE:
    self->az.max = 2865;
    self->el.max = 1417;
    break;
  }

  /* Conversion factor from cog offset to degree offset */
  self->az.deg_per_cog_hole = 0.125;
  self->el.deg_per_cog_hole = 0.125;
  
  /* Slow-margin cog values in az/el. */
  self->az.close = self->el.close = 128;
  self->az.very_close = self->el.very_close = 8;

  /* motor duty cycle management */
  self->mds_data.min = 40; /* ms */
  self->mds_data.max = 350; /* ms */
  self->mds_data.scale = 25; /* scale position delta (e.g. =25 yields exp(-1) when delta is 25) */
  
  /* changes telescope target position */
  self->az.requested = self->az.min;
  self->el.requested = self->el.min;
  /* current/target azimuth/elevation */
  self->az.current = self->az.target = 0;
  self->el.current = self->el.target = 0;
  
  /* initial cog status */
  self->az.detector_state = self->az.get_detector_state(self) ? ds_high : ds_low;
  self->el.detector_state = self->el.get_detector_state(self) ? ds_high : ds_low;
  
  RIO_start_monitoring_position(self);
  return 1;
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                           Reset telescope pointing                            *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * Move towards home at full motor speed until the end switches are hit
 * for both azimuth and elevation.
 */
static void
rp_to_home(RIO *self)
{
  self->az.set_motor_ccw_mode(self);
  self->el.set_motor_ccw_mode(self);
  self->az.start_motor(self);
  self->el.start_motor(self);

  /* move until end switches are hit */
  int az0, el0, az1, el1;
  do {
    az0 = self->az.current;
    el0 = self->el.current;
    sleep_ms(500);
    az1 = self->az.current;
    el1 = self->el.current;
    if (az1 == az0) {
      self->az.stop_motor(self);
      self->az.clear_motor_ccw_mode(self);
    }
    if (el1 == el0) {
      self->el.stop_motor(self);
      self->el.clear_motor_ccw_mode(self);
    }
  } while (az1 != az0 || el1 != el0);
}

/**
 * Move away from home at full motor speed for a given duration
 */
static void
rp_from_home(RIO *self,
	     int duration_ms)
{
  self->el.clear_motor_ccw_mode(self);
  self->az.clear_motor_ccw_mode(self);
  self->el.start_motor(self);
  self->az.start_motor(self);

  sleep_ms(duration_ms);

  self->el.stop_motor(self);
  self->az.stop_motor(self);

  /* wait for motors */
  sleep_ms(3000);
}

/**
 * Initialize telescope pointing to a known position.
 */
static void
RIO_reset_pointing(RIO *self)
{
  self->knowpos = false;
  self->stuck = false;

  rp_to_home(self);
  /* The telescope may reach home position at different speeds.
   * This can cause an offset from the physical (Az=0,El=0) position
   * by a few cogs.
   * briefly moving from home before returning to home should
   * remove this offset.
   */
  rp_from_home(self, 500);
  rp_to_home(self);

  self->az.current = 0;
  self->el.current = 0;
  self->az.requested = self->az.min;
  self->el.requested = self->el.min;
  
  self->knowpos = true;
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                               Monitor position                                *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */


/**
 * deduce the state of the detector given a number of samples
 */
static enum detector_state
mp_deduce_state(RIO *self,
		int j)
{
  return j == 0 ? ds_low : j == self->pos_samples ? ds_high : ds_undefined;
}

/**
 * sample the state of the azimuth and elevation detector
 */
static void
mp_sample_detector_state(RIO *self,
			 enum detector_state *s_az,
			 enum detector_state *s_el)
{
  int j_el = 0;
  int j_az = 0;
  double t_sleep = 0;
  for (int samples = self->pos_samples; samples--;) {
    t_sleep += 2e-3;
    double t_start = get_time();
    j_el += self->el.get_detector_state(self);
    j_az += self->az.get_detector_state(self);
    sleep_s(t_sleep - (get_time() - t_start));
    t_sleep -= get_time() - t_start;
  }
  *s_el = mp_deduce_state(self, j_el);
  *s_az = mp_deduce_state(self, j_az);
}

/**
 * update the state of the detector and display for the given axis.
 */
static void
mp_update_detector_state(RIO *self,
			 struct motor_axis *ax,
			 enum detector_state state)
{
  if (state != ds_undefined && state != ax->detector_state) {
    ax->detector_state = state;
    /* passed a cog/hole, update position */
    ax->current += ax->motor_ccw_mode(self) ? -1 : 1;
    ax->update_detector_status_led(self);
  }
}

/**
 * Monitor the position of the telescope.
 */
static RIO *
RIO_monitor_position(RIO *self)
{
  enum detector_state s_el = ds_undefined, s_az = ds_undefined;
  printf("Monitor position loop starting...\n");
  while (self->run_monitor_position) {
    mp_sample_detector_state(self, &s_az, &s_el);
    
    mp_update_detector_state(self, &self->el, s_el);
    mp_update_detector_state(self, &self->az, s_az);
  }
  printf("Monitor position loop exited.\n");
  self->knowpos = false;
  return self;
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                   Move loop                                   *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * axis-specific data for detetecting if the telescope is stuck.
 */
struct axis_stuck_detection {
  int same;
  int stop;
};

/**
 * axis-specific data for stopping the telescope.
 */
struct axis_stop_telescope {
  bool stop;
};

/**
 * Length of history record (in move-loops).
 */
#define HR_SIZE 0x8

/**
 * Mask for history traversion.
 */
#define HR_MASK 0x7

/**
 * Data structure for recording telescope position.
 */
struct axis_history {
  int history[HR_SIZE];
  int idx;
};

/**
 * Initialize position history record.
 */
static void
history_init(struct axis_history *ah)
{
  ah->idx = 0;
  memset(ah->history, 0, sizeof(ah->history));
}

/**
 * Append telescope's current position to history record.
 */
static void
history_append(struct axis_history *ah,
	       int current)
{
  ah->history[ah->idx] = current;
  ah->idx = (ah->idx+1) & HR_MASK;
}

/**
 * Check if all recorded positions (i.e. HR_SIZE latest entries) are equal.
 */
static int
history_all_equal(struct axis_history *ah)
{
  for (int i = 1; i < HR_SIZE; ++i) {
    if (ah->history[i-1] != ah->history[i]) {
      return 0;
    }
  }
  return 1;
}

/**
 * Retrieve the current/latest position in the record.
 */
static int
history_current(struct axis_history *ah)
{
  return ah->history[(ah->idx + HR_SIZE-1) & HR_MASK];
}

/**
 * Retrieve the previous position in the record.
 */
static int
history_most_recent(struct axis_history *ah)
{
  return ah->history[(ah->idx + HR_SIZE-2) & HR_MASK];
}

/**
 * Update the stuck detection for the given axis.
 */
static int
ml_check_stuck(RIO *self,
	       struct motor_axis *ax,
	       struct axis_stuck_detection *sd)
{
  if (sd->stop == ax->current && abs(ax->current - ax->target) > self->stuck_tol) {
    ++sd->same;
  } else {
    sd->same = 0;
    sd->stop = ax->current;
  }
  return self->stuck = sd->same > self->stuck_samples;
}

/**
 * Compute how long the motors should be turned on during the move loop
 * given a delta (target-current).
 */
static int
ml_compute_duty_cycle(struct motor_duty_cycle *mds, int delta)
{
  return (int) ((mds->max - mds->min) * (1 - exp(-sqr(delta/mds->scale))) + mds->min);
}

/**
 * Executes the move loop (i.e. run the motors).
 */
static void
ml_run_motors(RIO *self,
	      struct motor_axis *az,
	      struct motor_axis *el,
	      struct axis_history *az_ah,
	      struct axis_history *el_ah,
	      int run_az,
	      int run_el)
{
  int t_run_az = 0;
  if (run_az && az->target != history_current(az_ah)) {
    az->start_motor(self);
    t_run_az = ml_compute_duty_cycle(&self->mds_data, abs(az->target - history_current(az_ah)));
  }
  int t_run_el = 0;
  if (run_el && el->target != history_current(el_ah)) {
    el->start_motor(self);
    t_run_el = ml_compute_duty_cycle(&self->mds_data, abs(el->target - history_current(el_ah)));
  }

  int t_rem = self->mds_data.max;
  if (t_run_az > t_run_el) {
    if (t_run_el) {
      sleep_ms(t_run_el);
      el->stop_motor(self);
    }
    sleep_ms(t_run_az - t_run_el);
    az->stop_motor(self);
    t_rem -= t_run_az;
  } else if (t_run_az < t_run_el) {
    if (t_run_az) {
      sleep_ms(t_run_az);
      az->stop_motor(self);
    }
    sleep_ms(t_run_el - t_run_az);
    el->stop_motor(self);
    t_rem -= t_run_el;
  } else {
    if (t_run_az) {
      sleep_ms(t_run_az);
      az->stop_motor(self);
      el->stop_motor(self);
      t_rem -= t_run_az;
    }
  }
  sleep_ms(t_rem);
}

/**
 * initialize stop motor on the given axis.
 */
static void
ml_initialize_stop(RIO *self,
		   struct motor_axis *ax,
		   struct axis_stop_telescope *st)
{
  st->stop = true;
  ax->stop_motor(self);
}

/**
 * clear stop azimuth motors.
 */
static void
ml_clear_stop(RIO *self,
	      struct motor_axis *ax,
	      struct axis_stop_telescope *st)
{
  (void)self;
  st->stop = false;
  ax->target = ax->current;
}

/**
 * select and set up action (stop or move) for current move loop
 * on the given axis, given that the telescope target have changed.
 */
static void
ml_select_action_new_target(RIO *self,
			    struct motor_axis *ax,
			    struct axis_stop_telescope *st,
			    int new_target,
			    struct axis_history *ah)
{
  int current = history_current(ah);
  int current_delta = ax->target - current;
  int next_delta = new_target - current;
  if (next_delta < 0) {
    /* ccw mode next */
    if (current_delta > 0) {
      /* new target in different direction */
      ml_initialize_stop(self, ax, st);
    } else if (current_delta < 0) {
      /* new target in same direction */
      if (ax->motor_ccw_mode(self)) {
	/* ccw mode currently (same direction) */
	ax->target = new_target;
      } else {
	/* cw mode currently (different direction) */
	ml_initialize_stop(self, ax, st);
      }
    } else {
      /* currently at current target */
      if (ax->motor_ccw_mode(self)) {
	/* ccw mode currently (same direction) */
	ax->target = new_target;
      } else {
	/* cw mode currently (different direction) */
	if (history_all_equal(ah)) {
	  /* not moving */
	  ax->target = new_target;
	  ax->set_motor_ccw_mode(self);
	} else {
	  /* (maybe) moving */
	  ml_initialize_stop(self, ax, st);
	}
      }
    }
  } else if (next_delta > 0) {
    /* cw mode next */
    if (current_delta < 0) {
      /* new target in different direction */
      ml_initialize_stop(self, ax, st);
    } else if (current_delta > 0) {
      /* new target in same direction */
      if (ax->motor_ccw_mode(self)) {
	/* ccw mode currently (different direction) */
	ml_initialize_stop(self, ax, st);
      } else {
	/* cw mode currently (same direction) */
	ax->target = new_target;
      }
    } else {
      /* currently at current target */
      if (ax->motor_ccw_mode(self)) {
	/* ccw mode currently (different direction) */
	if (history_all_equal(ah)) {
	  /* not moving */
	  ax->target = new_target;
	  ax->clear_motor_ccw_mode(self);
	} else {
	  /* (maybe) moving */
	  ml_initialize_stop(self, ax, st);
	}
      } else {
	/* cw mode currently (same direction) */
	ax->target = new_target;
      }
    }
  } else {
    /* currently at new target (direction may be different) */
    ml_initialize_stop(self, ax, st);
  }
}

/**
 * select and set up action (stop or move) for current move loop
 * on the given axis, given that the telescope target have not changed.
 */
static void
ml_select_action_same_target(RIO *self,
			     struct motor_axis *ax,
			     struct axis_stop_telescope *st,
			     struct axis_history *ah)
{
  int current = history_current(ah);
  int prev = history_most_recent(ah);
  int current_delta = ax->target - current;
  int prev_delta = ax->target - prev;
  if (current_delta < 0) {
    if (prev_delta < 0) {
      /* continue in the same direction */
      if (abs(current_delta) > abs(prev_delta)) {
	/* error: the direction is incorrect */
	ml_initialize_stop(self, ax, st);
      }
    } else {
      /* telescope have overshot target */
      ml_initialize_stop(self, ax, st);
    }
  } else if (current_delta > 0) {
    if (prev_delta > 0) {
      /* continue in the same direction */
      if (abs(current_delta) > abs(prev_delta)) {
	/* error: the direction is incorrect */
	ml_initialize_stop(self, ax, st);
      }
    } else {
      /* telescope have overshot target */
      ml_initialize_stop(self, ax, st);
    }
  } else {
    /* currently at or arrived at target */
  }
}

/**
 * select and set up action (stop or move) for current move loop
 * on the given axis.
 */
static void
ml_select_action(RIO *self,
		 struct motor_axis *ax,
		 struct axis_stop_telescope *st,
		 int target,
		 struct axis_history *prev)
{
  if (st->stop) {
    if (history_all_equal(prev)) {
      ml_clear_stop(self, ax, st);
    }
  } else {
    if (ax->target == target) {
      ml_select_action_same_target(self, ax, st, prev);
    } else {
      ml_select_action_new_target(self, ax, st, target, prev);
    }
  }
}

/**
 * Routine that moves the telescope to requested positions.
 */
static RIO *
RIO_move_loop(RIO *self)
{
  RIO_reset_pointing(self);
  
  struct axis_stop_telescope az_st = { false }, el_st = { false };
  struct axis_stuck_detection az_sd = { 0, self->az.current }, el_sd = { 0, self->el.current };
  struct axis_history az_ah, el_ah;
  history_init(&az_ah);
  history_init(&el_ah);

  printf("Move loop starting...\n");
  while (self->run_move_loop) {
    int target_az = clip(self->az.requested, self->az.min, self->az.max);
    history_append(&az_ah, self->az.current);
    ml_select_action(self, &self->az, &az_st, target_az, &az_ah);
    
    int target_el = clip(self->el.requested, self->el.min, self->el.max);
    history_append(&el_ah, self->el.current);
    ml_select_action(self, &self->el, &el_st, target_el, &el_ah);

    ml_run_motors(self, &self->az, &self->el, &az_ah, &el_ah, !az_st.stop, !el_st.stop);

    if (ml_check_stuck(self, &self->az, &az_sd) || ml_check_stuck(self, &self->el, &el_sd)) {
      /* Telescope is stuck */
      break;
    }
  }
  printf("Move loop exited.\n");

  self->az.stop_motor(self);
  self->el.stop_motor(self);
  self->az.clear_motor_ccw_mode(self);
  self->el.clear_motor_ccw_mode(self);
  self->knowpos = false;
  return self;
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                 RIO interface                                 *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

void
RIO_set_lna(RIO *self)
{
  dish_set_lna(self);
}
void
RIO_clear_lna(RIO *self)
{
  dish_clear_lna(self);
}
void
RIO_set_diode(RIO *self)
{
  dish_set_diode(self);
}
void
RIO_clear_diode(RIO *self)
{
  dish_clear_diode(self);
}

double
get_minaz(RIO *self)
{
  return self->az.min;
}

void
set_minaz(RIO *self,
	  double minaz)
{
  self->az.min = (int) minaz;
}

double
get_minel(RIO *self)
{
  return self->el.min;
}

void
set_minel(RIO *self,
	  double minel)
{
  self->el.min = (int) minel;
}

double
get_maxaz(RIO *self)
{
  return self->az.max;
}

void
set_maxaz(RIO *self,
	  double maxaz)
{
  self->az.max = (int) maxaz;
}

double
get_maxel(RIO *self)
{
  return self->el.max;
}

void
set_maxel(RIO *self,
	  double maxel)
{
  self->el.max = (int) maxel;
}

double
get_az_dpch(RIO *self)
{
  return self->az.deg_per_cog_hole;
}

void
set_az_dpch(RIO *self,
	    double az_dpch)
{
  self->az.deg_per_cog_hole = az_dpch;
}

double
get_el_dpch(RIO *self)
{
  return self->el.deg_per_cog_hole;
}

void
set_el_dpch(RIO *self,
	    double el_dpch)
{
  self->el.deg_per_cog_hole = el_dpch;
}

double
get_cls_az(RIO *self)
{
  return self->az.close;
}

void
set_cls_az(RIO *self,
	   double cls_az)
{
  self->az.close = (int) cls_az;
}

double
get_cls_el(RIO *self)
{
  return self->el.close;
}

void
set_cls_el(RIO *self,
	   double cls_el)
{
  self->el.close = (int) cls_el;
}

double
get_vcls_az(RIO *self)
{
  return self->az.very_close;
}

void
set_vcls_az(RIO *self,
	    double vcls_az)
{
  self->az.very_close = (int) vcls_az;
}

double
get_vcls_el(RIO *self)
{
  return self->el.very_close;
}

void
set_vcls_el(RIO *self,
	    double vcls_el)
{
  self->el.very_close = (int) vcls_el;
}

double
get_samples(RIO *self)
{
  return self->pos_samples;
}

void
set_samples(RIO *self,
	    double samples)
{
  self->pos_samples = (int) samples;
}

double
get_c_az(RIO *self)
{
  return self->az.current;
}

double
get_c_el(RIO *self)
{
  return self->el.current;
}

double
get_t_az(RIO *self)
{
  return self->az.requested;
}

void
set_t_az(RIO *self,
	 double t_az)
{
  self->az.requested = (int) t_az;
}

double
get_t_el(RIO *self)
{
  return self->el.requested;
}

void
set_t_el(RIO *self,
	 double t_el)
{
  self->el.requested = (int) t_el;
}

double
get_knowpos(RIO *self)
{
  return self->knowpos ? 1 : 0;
}

void
set_knowpos(RIO *self,
	    double knowpos)
{
  self->knowpos = (int) knowpos ? true : false;
}

double
get_stuck(RIO *self)
{
  return self->stuck ? 1 : 0;
}

void
set_stuck(RIO *self,
	  double stuck)
{
  self->stuck = (int) stuck ? true : false;
}

double
get_tol(RIO *self)
{
  return self->stuck_tol;
}

void
set_tol(RIO *self,
	double stuck_tol)
{
  self->stuck_tol = (int) stuck_tol;
}

double
get_stks(RIO *self)
{
  return self->stuck_samples;
}

void
set_stks(RIO *self,
	 double stks)
{
  self->stuck_samples = (int) stks;
}

/* Deprecated */

double
get_close_az(RIO *self)
{
  (void)self; return 12;
}

void
set_close_az(RIO *self,
	     double close_az)
{
  (void)self; (void)close_az;
}

double
get_close_el(RIO *self)
{
  (void)self; return 12;
}

void
set_close_el(RIO *self,
	     double close_el)
{
  (void)self; (void)close_el;
}

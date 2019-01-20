#ifndef RIO_H_INCLUDED
#define RIO_H_INCLUDED

#include <stdint.h>

/**
 * Target system for the virtual RIO.
 * Used for targer-specific settings.
 */
enum system_host {
  VALE,
  BRAGE
};

typedef struct RIO_t RIO;

/**
 * Allocates space for the virtual RIO and initializes is
 * it to a virtual power-on state in addition to resetting
 * the physical RIO to a power-on state.
 */
RIO *RIO_new(enum system_host target, char const *host, uint16_t port);

/**
 * Releases all resources allocated by the virtual RIO (including
 * the connection to the physical RIO).
 */
void RIO_delete(RIO *self);

/**
 * Start the thread that moves the telescope to requested positions.
 */
void RIO_start_move_loop(RIO *self);

/**
 * Stop the thread that moves the telescope to requested positions.
 */
void RIO_stop_move_loop(RIO *self);

/**
 * Reset the virtual and physical RIO to a power-on state.
 */
int RIO_hard_reset(RIO *self);

/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                 RIO interface                                 *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

void RIO_set_lna(RIO *self);
void RIO_clear_lna(RIO *self);
void RIO_set_diode(RIO *self);
void RIO_clear_diode(RIO *self);
double get_minaz(RIO *self);
void   set_minaz(RIO *self, double minaz);
double get_minel(RIO *self);
void   set_minel(RIO *self, double minel);
double get_maxaz(RIO *self);
void   set_maxaz(RIO *self, double maxaz);
double get_maxel(RIO *self);
void   set_maxel(RIO *self, double maxel);
double get_az_dpch(RIO *self);
void   set_az_dpch(RIO *self, double az_dpch);
double get_el_dpch(RIO *self);
void   set_el_dpch(RIO *self, double el_dpch);
double get_cls_az(RIO *self);
void   set_cls_az(RIO *self, double cls_az);
double get_cls_el(RIO *self);
void   set_cls_el(RIO *self, double cls_el);
double get_vcls_az(RIO *self);
void   set_vcls_az(RIO *self, double vcls_az);
double get_vcls_el(RIO *self);
void   set_vcls_el(RIO *self, double vcls_el);
double get_samples(RIO *self);
void   set_samples(RIO *self, double samples);
double get_c_az(RIO *self);
double get_c_el(RIO *self);
double get_t_az(RIO *self);
void   set_t_az(RIO *self, double t_az);
double get_t_el(RIO *self);
void   set_t_el(RIO *self, double t_el);
double get_knowpos(RIO *self);
void   set_knowpos(RIO *self, double knowpos);
double get_stuck(RIO *self);
void   set_stuck(RIO *self, double stuck);
double get_tol(RIO *self);
void   set_tol(RIO *self, double tol);
double get_stks(RIO *self);
void   set_stks(RIO *self, double stks);

/* Deprecated */
double get_close_az(RIO *self);
void   set_close_az(RIO *self, double close_az);
double get_close_el(RIO *self);
void   set_close_el(RIO *self, double close_el);

#endif /* RIO_H_INCLUDED */

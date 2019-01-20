#ifndef PROGRESSBAR_H_
#define PROGRESSBAR_H_

typedef enum {
  pbt_no_color,
  pbt_one_color,
  pbt_frac_color
} ProgressbarType;

typedef struct {
  unsigned rows;
  char left_edge;
  char right_edge;
  char fill;
  char fill_last;
  char empty;
  ProgressbarType type;
} ProgressbarConfig;

extern ProgressbarConfig
get_default_config(void);

extern int
create_progressbar(ProgressbarConfig const *pc);
extern void
destroy_progressbar(void);

extern void
draw_progressbar(unsigned row,
		 char const *msg,
		 double percent);

#endif /* PROGRESSBAR_H_ */

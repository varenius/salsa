#define _POSIX_SOURCE

#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include <errno.h>
#include <unistd.h>
#include <signal.h>
#include <sys/ioctl.h>

#include "progressbar.h"
#include "defs.h"

#define _N_C 6
static char const _c_frac[_N_C][ANSI_COLOR_SIZE] = {
  ANSI_RED_FG, ANSI_BRIGHT_RED_FG,
  ANSI_YELLOW_FG, ANSI_BRIGHT_YELLOW_FG,
  ANSI_GREEN_FG, ANSI_BRIGHT_GREEN_FG
};
static char const _c_max[] = ANSI_BRIGHT_CYAN_FG;
static char const _c_one[] = ANSI_GREEN_FG;
#define _C_RST ANSI_RESTORE_FG

#define DEFAULT_CONFIG_INIT { 0, '[', ']', '#', '#', '.', pbt_no_color }
static ProgressbarConfig default_config = DEFAULT_CONFIG_INIT, cfg = DEFAULT_CONFIG_INIT;

static struct {
  int _rows;
  int _cols;
} tsize;

typedef struct {
  int row;
  char *progress_text;
  double percent_done;
} ProgressbarRow;

static struct {
  unsigned _rows;
  ProgressbarRow *_update_info;
  pthread_mutex_t __mtx;
  char const *(*cs)(double);
} prgbar;

#define MAX_PRCNT_CHARS 6
#define PRCNT_ALLOC_SIZE MAX_PRCNT_CHARS + 1
#define MAX_PBAR_LENGTH 0x1000
#define PBAR_ALLOC_SIZE (MAX_PBAR_LENGTH+1 + 2*ANSI_CS_ALLOC_SIZE)
static struct {
  char bar[PBAR_ALLOC_SIZE];
  char pcnt[PRCNT_ALLOC_SIZE];
  char cs[ANSI_CS_ALLOC_SIZE];
  char tmp[ANSI_CS_ALLOC_SIZE];
} bfr;

static struct sigaction sa_sigwinch;

#define EXIT(status, ...) { fprintf(stderr, __VA_ARGS__); exit(status); }
#define EXIT_SIGINIT(signum) EXIT(signum, "Error initializing " #signum " handler: %s\n", strerror(errno))
#define FREE(ptr) free(ptr); ptr = NULL
#define CPY_TO_BUFFER(SRC) strncpy(bfr.cs, SRC, ANSI_CS_ALLOC_SIZE)
#define ANSI_COLOR(FG) CPY_TO_BUFFER(ansi_color(bfr.tmp, FG))
#define ANSI_CURSOR_UP(STEPS) CPY_TO_BUFFER(ansi_cursor_up(bfr.tmp, STEPS))
#define ANSI_CURSOR_DOWN(STEPS) CPY_TO_BUFFER(ansi_cursor_down(bfr.tmp, STEPS))
#define ANSI_CURSOR_FORWARD(STEPS) CPY_TO_BUFFER(ansi_cursor_forward(bfr.tmp, STEPS))
#define ANSI_CURSOR_BACK(STEPS) CPY_TO_BUFFER(ansi_cursor_back(bfr.tmp, STEPS))
#define ANSI_SET_SCROLL_REGION(top, bottom) CPY_TO_BUFFER(ansi_set_scroll_region(bfr.tmp, top+1, bottom))
#define ANSI_CURSOR_POSITION(row, col) CPY_TO_BUFFER(ansi_cursor_position(bfr.tmp, row+1, col))

#define __OFILE stdout
#define WRITEF(...) fprintf(__OFILE, __VA_ARGS__)
#define FLUSH() fflush(__OFILE)
#define FLOCK() { flockfile(__OFILE); pthread_mutex_lock(&prgbar.__mtx); }
#define FUNLOCK() { pthread_mutex_unlock(&prgbar.__mtx); funlockfile(__OFILE); }

#define CHOOSE_CS() (cfg.type == pbt_frac_color				\
		     ? progress_frac_color				\
		     : cfg.type == pbt_one_color ? progress_one_color	\
		     : progress_no_color)

static void setup_terminal_scroll_region(int bottom, int top);
static void restore_terminal_scroll_region(void);
static void update_terminal_size(void);
static int init_sigaction(struct sigaction *sa, int signum, void (*sa_handler)(int));
static void sigwinch_handler(int sig);
static char const *progress_no_color(double fraction);
static char const *progress_one_color(double fraction);
static char const *progress_frac_color(double fraction);
static char const *prog_bar(char * const dst, char const *fill_color, int const s_fill, int const s_pbar);
static char const *prgbar_percent(char *dst, double pcnt);
static void print_progressbar(ProgressbarRow const *p);

static double clip(double v, double max, double min) { return v > max ? max : v < min ? min : v; }
static int max(int a, int b) { return a > b ? a : b; }
static int min(int a, int b) { return a < b ? a : b; }

static void
setup_terminal_scroll_region(int top,
			     int bottom)
{
  int i;
  
  for (i = prgbar._rows; i-- > 0; WRITEF("%c", '\n'));
  WRITEF(ANSI_SAVE_CURSOR);
  WRITEF("%s", ANSI_SET_SCROLL_REGION(top, bottom));
  WRITEF(ANSI_RESTORE_CURSOR);
  if (prgbar._rows > 0) {
    WRITEF("%s", ANSI_CURSOR_UP(prgbar._rows));
  }
  FLUSH();
}

static void
restore_terminal_scroll_region(void)
{
  WRITEF(ANSI_SAVE_CURSOR);
  WRITEF(ANSI_SCROLL_RESTORE);
  WRITEF(ANSI_RESTORE_CURSOR);
  WRITEF("%s", ANSI_CURSOR_DOWN(prgbar._rows));
  FLUSH();
}

static void
update_terminal_size(void)
{
  struct winsize w;
  
  ioctl(STDOUT_FILENO, TIOCGWINSZ, &w);
  tsize._rows = w.ws_row;
  tsize._cols = w.ws_col;
}

static int
init_sigaction(struct sigaction *sa,
	       int signum,
	       void (*sa_handler)(int))
{
  sigemptyset(&sa->sa_mask);
  sa->sa_flags = 0;
  sa->sa_handler = sa_handler;
  return sigaction(signum, sa, NULL);
}

static void
sigwinch_handler(int sig)
{
  ProgressbarRow *p;
  (void)sig;

  signal(SIGWINCH, SIG_IGN);
  FLOCK();
  update_terminal_size();
  setup_terminal_scroll_region(0, tsize._rows - prgbar._rows);
  for (p = prgbar._update_info; p != prgbar._update_info + prgbar._rows; ++p) {
    print_progressbar(p);
  }
  FUNLOCK();
  signal(SIGWINCH, sigwinch_handler);
}

static char const *progress_no_color(double fraction) { (void)fraction; return NULL; }
static char const *progress_one_color(double fraction) { (void)fraction; return _c_one; }
static char const *progress_frac_color(double fraction) {
  return fraction > 1 ? _c_max : _c_frac[(int) max(0, min(_N_C-1, fraction * _N_C))];
}

static char const *
prog_bar(char * const dst,
	 char const *fill_color,
	 int const s_fill,
	 int const s_pbar)
{
  char *_dst = dst;
  int const has_edge = s_fill < s_pbar;
  int i;

  if (fill_color) {
    _dst += _SNPRINTF(_dst, ANSI_CS_ALLOC_SIZE, "%s", ANSI_COLOR(fill_color));
  }
  for (i = s_fill - (has_edge ? 1 : 0); i-- > 0;) {
    _dst += _SNPRINTF(_dst, 2, "%c", cfg.fill);
  }
  if (has_edge && s_fill > 0) {
    _dst += _SNPRINTF(_dst, 2, "%c", cfg.fill_last);
  }
  if (fill_color) {
    _dst += _SNPRINTF(_dst, ANSI_CS_ALLOC_SIZE, "%s", ANSI_COLOR(_C_RST));
  }
  for (i = s_pbar-s_fill; i-- > 0;) {
    _dst += _SNPRINTF(_dst, 2, "%c", cfg.empty);
  }
  return dst;
}

static char const *
prgbar_percent(char *dst,
	       double pcnt)
{
  if (pcnt > 100) {
    _SNPRINTF(dst, PRCNT_ALLOC_SIZE, ">100.0");
  } else {
    _SNPRINTF(dst, PRCNT_ALLOC_SIZE, "%6.1f", pcnt);
  }
  return dst;
}

static void
print_progressbar(ProgressbarRow const *p)
{
  int padding = 6;	   /* everything but progress text, pcnt and bar */
  int s_pbar = min(tsize._cols - padding - (strlen(p->progress_text) + MAX_PRCNT_CHARS),
		   MAX_PBAR_LENGTH);
  int s_fill = (int) (clip(p->percent_done/100.0, 1, 0)*s_pbar + 0.5);

  WRITEF(ANSI_SAVE_CURSOR);
  WRITEF("%s", ANSI_CURSOR_POSITION(tsize._rows - (prgbar._rows-p->row), 0));
  WRITEF("%s %s%% %c%s%c ", p->progress_text, prgbar_percent(bfr.pcnt, p->percent_done),
	 cfg.left_edge,
	 prog_bar(bfr.bar, prgbar.cs(p->percent_done/100.0), s_fill, s_pbar),
	 cfg.right_edge);
  WRITEF(ANSI_RESTORE_CURSOR);
  FLUSH();
}

extern ProgressbarConfig
get_default_config(void)
{
  return default_config;
}

extern void
draw_progressbar(unsigned row,
		 char const *msg,
		 double pcnt)
{
  ProgressbarRow *p = row < prgbar._rows ? &prgbar._update_info[row] : NULL;
  size_t n_chars = strlen(msg) + 1;
  
  FLOCK();
  if (p) {
    p->progress_text = strncpy(realloc(p->progress_text, n_chars * sizeof(char)), msg, n_chars);
    p->percent_done = pcnt;
    print_progressbar(p);
  }
  FUNLOCK();
}

extern int
create_progressbar(ProgressbarConfig const *pc)
{
  ProgressbarRow *p;
  unsigned i;

  if (init_sigaction(&sa_sigwinch, SIGWINCH, sigwinch_handler) == -1) {
    EXIT_SIGINIT(SIGWINCH);
  }

  update_terminal_size();
  if (pc) {
    memcpy(&cfg, pc, sizeof(ProgressbarConfig));
  }
  prgbar.cs = CHOOSE_CS();
  prgbar._rows = cfg.rows;
  prgbar._update_info = (ProgressbarRow *) calloc(prgbar._rows, sizeof(ProgressbarRow));
  for (i = 0; i < prgbar._rows; ++i) {
    p = &prgbar._update_info[i];
    p->row = i;
    p->progress_text = (char *) calloc(1, sizeof(char));
  }
  
  setup_terminal_scroll_region(0, tsize._rows-prgbar._rows);
  return 0;
}

extern void
destroy_progressbar(void)
{
  ProgressbarRow *p;
  unsigned i;
  
  for (i = prgbar._rows; i-- > 0;) {
    WRITEF("%s" ANSI_DEL_LINE, ANSI_CURSOR_POSITION(tsize._rows - (prgbar._rows-i), 0));
  }
  FLUSH();
  restore_terminal_scroll_region();
  
  for (p = prgbar._update_info; p != prgbar._update_info + prgbar._rows; ++p) {
    FREE(p->progress_text);
  }
  prgbar._rows = 0;
  FREE(prgbar._update_info);
}

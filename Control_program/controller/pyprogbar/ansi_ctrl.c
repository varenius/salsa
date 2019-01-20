#include "defs.h"
#include <stdio.h>

char const *ansi_color(char *__bfr, char const *fg) {
  _SNPRINTF(__bfr, ANSI_CS_ALLOC_SIZE, ANSI_CTRL_SEQ "%sm", fg);
  return __bfr;
}
char const *ansi_cursor_up(char *__bfr, int steps) {
  _SNPRINTF(__bfr, ANSI_CS_ALLOC_SIZE, ANSI_CTRL_SEQ "%dA", steps);
  return __bfr;
}
char const *ansi_cursor_down(char *__bfr, int steps) {
  _SNPRINTF(__bfr, ANSI_CS_ALLOC_SIZE, ANSI_CTRL_SEQ "%dB", steps);
  return __bfr;
}
char const *ansi_cursor_forward(char *__bfr, int steps) {
  _SNPRINTF(__bfr, ANSI_CS_ALLOC_SIZE, ANSI_CTRL_SEQ "%dC", steps);
  return __bfr;
}
char const *ansi_cursor_back(char *__bfr, int steps) {
  _SNPRINTF(__bfr, ANSI_CS_ALLOC_SIZE, ANSI_CTRL_SEQ "%dD", steps);
  return __bfr;
}
char const *ansi_set_scroll_region(char *__bfr, int top, int bottom) {
  _SNPRINTF(__bfr, ANSI_CS_ALLOC_SIZE, ANSI_CTRL_SEQ "%d;%dr", top, bottom);
  return __bfr;
}
char const *ansi_cursor_position(char *__bfr, int row, int col) {
  _SNPRINTF(__bfr, ANSI_CS_ALLOC_SIZE, ANSI_CTRL_SEQ "%d;%df", row, col);
  return __bfr;
}

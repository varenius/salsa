#ifndef PROGRESSBAR_DEFS_H_
#define PROGRESSBAR_DEFS_H_

#define ANSI_BLACK_FG "30"
#define ANSI_RED_FG "31"
#define ANSI_GREEN_FG "32"
#define ANSI_YELLOW_FG "33"
#define ANSI_BLUE_FG "34"
#define ANSI_MAGENTA_FG "35"
#define ANSI_CYAN_FG "36"
#define ANSI_WHITE_FG "37"
#define ANSI_RESTORE_FG "39"
#define ANSI_BRIGHT_BLACK_FG "90"
#define ANSI_BRIGHT_RED_FG "91"
#define ANSI_BRIGHT_GREEN_FG "92"
#define ANSI_BRIGHT_YELLOW_FG "93"
#define ANSI_BRIGHT_BLUE_FG "94"
#define ANSI_BRIGHT_MAGENTA_FG "95"
#define ANSI_BRIGHT_CYAN_FG "96"
#define ANSI_BRIGHT_WHITE_FG "97"

#define ANSI_BLACK_BG "40"
#define ANSI_RED_BG "41"
#define ANSI_GREEN_BG "42"
#define ANSI_YELLOW_BG "43"
#define ANSI_BLUE_BG "44"
#define ANSI_MAGENTA_BG "45"
#define ANSI_CYAN_BG "46"
#define ANSI_WHITE_BG "47"
#define ANSI_RESTORE_BG "49"
#define ANSI_BRIGHT_BLACK_BG "100"
#define ANSI_BRIGHT_RED_BG "101"
#define ANSI_BRIGHT_GREEN_BG "102"
#define ANSI_BRIGHT_YELLOW_BG "103"
#define ANSI_BRIGHT_BLUE_BG "104"
#define ANSI_BRIGHT_MAGENTA_BG "105"
#define ANSI_BRIGHT_CYAN_BG "106"
#define ANSI_BRIGHT_WHITE_BG "107"

#define ANSI_COLOR_SIZE 4

#define ASCII_ESCAPE "\033"
#define ANSI_CTRL_SEQ ASCII_ESCAPE "["
#define ANSI_SAVE_CURSOR ASCII_ESCAPE "7"
#define ANSI_RESTORE_CURSOR ASCII_ESCAPE "8"
#define ANSI_DEL_TO_EOL ANSI_CTRL_SEQ "K"
#define ANSI_DEL_TO_SOL ANSI_CTRL_SEQ "1K"
#define ANSI_DEL_LINE ANSI_CTRL_SEQ "2K"
#define ANSI_DEL_DOWN ANSI_CTRL_SEQ "J"
#define ANSI_DEL_UP ANSI_CTRL_SEQ "1J"
#define ANSI_DEL_SCREEN ANSI_CTRL_SEQ "2J"
#define ANSI_FOREGROUND(C) ANSI_CTRL_SEQ C "m"

#define ANSI_SCROLL_DOWN ASCII_ESCAPE "D"
#define ANSI_SCROLL_UP ASCII_ESCAPE "M"
#define ANSI_SCROLL_RESTORE ANSI_CTRL_SEQ "r"
#define ANSI_DISABLE_WRAP ANSI_CTRL_SEQ "7l"
#define ANSI_ENABLE_WRAP ANSI_CTRL_SEQ "7h"

#define ANSI_CS_ALLOC_SIZE 0x1f

char const *ansi_color(char *__bfr, char const *fg);
char const *ansi_cursor_up(char *__bfr, int steps);
char const *ansi_cursor_down(char *__bfr, int steps);
char const *ansi_cursor_forward(char *__bfr, int steps);
char const *ansi_cursor_back(char *__bfr, int steps);
char const *ansi_set_scroll_region(char *__bfr, int top, int bottom);
char const *ansi_cursor_position(char *__bfr, int row, int col);

#ifdef _BSD_SOURCE
 #define _SNPRINTF(__bfr, max_size, ...) snprintf(__bfr, max_size, __VA_ARGS__)
#elif (__STDC_VERSION__ >= 199901L) || (_XOPEN_SOURCE >= 500) || _ISOC99_SOURCE || (_POSIX_C_SOURCE >= 200112L)
 #define _SNPRINTF(__bfr, max_size, ...) snprintf(__bfr, max_size, __VA_ARGS__)
#else
 #define _SNPRINTF(__bfr, max_size, ...) sprintf(__bfr, __VA_ARGS__)
#endif

#endif /* PROGRESSBAR_DEFS_H_ */

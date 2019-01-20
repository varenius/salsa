#include <ctype.h>
#include <string.h>

char *
lstrip(char *s)
{
  if (!s || !*s) {
    return s;
  }
  while (isspace(*s)) {
    *s++ = '\0';
  }
  return s;
}

char *
rstrip(char *s)
{
  if (!s || !*s) {
    return s;
  }
  char *end = s + strlen(s);
  while (--end != s && isspace(*end)) {
    *end = '\0';
  }
  return s;
}

char *
strip(char* s)
{
  return rstrip(lstrip(s));
}

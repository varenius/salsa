#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

#define HAS_GCLIB

#ifdef HAS_GCLIB
#include <gclibo.h>
#endif

#ifdef HAS_GCLIB
#define BFR_SIZE 0x4000
static char buf[BFR_SIZE];
#endif
#define IP_BFR_SIZE 0x10
static char ipbuf[IP_BFR_SIZE];
#define MAC_BFR_SIZE 0x12
static char macbuf[MAC_BFR_SIZE];
#ifdef HAS_GCLIB
static GCon g;

/**
 * Checks for errors returned from gclib functions.
 * If error was found the error code is printed and
 * the program exits.
 */
static void
check(GReturn rc)
{
  if (rc != G_NO_ERROR) {
    fprintf(stderr, "ERROR: %d\n", rc);
    if (g) {
      GClose(g);
    }
    exit(rc);
  }
}
#endif

/**
 * reads bytes integer values from str and places them
 * in in order of appearance in byte_vals.
 * The values in str are separated by delim and are
 * formatted in base base.
 */
static int
is_valid(char const *str,
	 int *byte_vals,
	 size_t bytes,
	 size_t base,
	 char delim)
{
  size_t len = strlen(str)+1;
  char *s;
  char * const __s = s = (char *) calloc(len, sizeof(char));
  strncpy(s, str, len);
  for (unsigned i = 0; *s && i < bytes; ++s) {
    char *end = s;
    int val = strtol(s, &end, base); /* read int from s */
    if (end != s) {		     /* an int was found in s, */
      s = end;			     /* move s past the int value */
      byte_vals[i] = val;	     /* and add it to the list */
    }
    if (*s == delim) {		/* move to next slot in byte_vals */
      ++i;			/* when delimiter is found */
    }
  }
  free(__s);
  
  for (unsigned i = 0; i < bytes; ++i) { /* check that all values are valid */
    if (byte_vals[i] < 0 || byte_vals[i] > 255) {
      return 0;
    }
  }
  return 1;
}

/**
 * Checks if buf is a string representing a valid MAC-address.
 */
static int
valid_mac(char const *buf)
{
  int mac[] = { -1, -1, -1, -1, -1, -1 };
  if(is_valid(buf, mac, 6, 16, ':')) { /* valid input, recreate MAC-address */
    char tmp[0x12];		       /* and verify that it is same as input */
    snprintf(tmp, 0x12, "%02X:%02X:%02X:%02X:%02X:%02X",
	     mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    return strncmp(tmp, buf, 0x12) == 0;
  }
  return 0;
}

/**
 * Checks if buf is a string representing a valid ipv4-address.
 */
static int
valid_ip(char const *buf)
{
  int ip[] = { -1, -1, -1, -1 };
  if(is_valid(buf, ip, 4, 10, '.')) { /* valid input, recreate MAC-address */
    char tmp[0x10];		      /* and verify that it is same as input */
    snprintf(tmp, 0x10, "%d.%d.%d.%d",
	     ip[0], ip[1], ip[2], ip[3]);
    return strncmp(tmp, buf, 0x10) == 0;
  }
  return 0;
}

/**
 * Clears stdin from any remaining input.
 */
static void
clrf(FILE *file)
{
  char c;
  while ((c = fgetc(file)) != '\n' && c != EOF);
}

/**
 * Requests a MAC-address from stdin and returns it if it is valid,
 * otherwise NULL.
 */
static char const *
req_mac(char *buf)
{
  printf("Enter the MAC address of the device (e.g. '00:50:4C:28:0D:5E'):\nMAC: ");
  if (!fscanf(stdin, "%17s", buf)) { return NULL; }
  clrf(stdin);
  printf("\n");
  return valid_mac(buf) ? buf : NULL;
}

/**
 * Requests a ipv4-address from stdin and returns it if it is valid,
 * otherwise NULL.
 */
static char const *
req_ip(char *buf)
{
  printf("Enter a new IPv4 address to assign the device (e.g. '169.254.212.76'):\nIPv4: ");
  if (!fscanf(stdin, "%15s", buf)) { return NULL; }
  clrf(stdin);
  printf("\n");
  return valid_ip(buf) ? buf : NULL;
}

int
main()
{
  char c;
  printf("DISCLAIMER:\n"
	 "This program will attempt to help you assign an ip to a RIO\n"
	 "device via ethernet in case it does not currently have one.\n"
	 "The ip you assign to the RIO should be on the same subnet as\n"
	 "the network interface that is used to communicate with it.\n"
	 "Once the RIO have been assigned an ip address, it must be\n"
	 "reset to factory defaults in order to set another with this\n"
	 "method, so be careful not to assign it to a different subnet.\n"
	 "If this method should not work for some reason, you have to\n"
	 "go to the physical location of the device and connecto to it\n"
	 "via serial and assign an ip address using the command IA.\n"
	 "\n"
	 "Proceed? [y/n] ");
  if ((c = getchar()) != 'y') {
    printf("Exiting...\n");
    return EXIT_SUCCESS;
  }
  
#ifdef HAS_GCLIB
  check(GAddresses(buf, BFR_SIZE));
  if (*buf) {
    printf("Units with an IP:\n%s\n\n", buf);
  } else {
    printf("There are no connected units with an assigned IP.\n");
  }
  check(GIpRequests(buf, BFR_SIZE));
  if (*buf == '\0' || *buf == '\n') {
    printf("There are no connected units without an assigned IP.\n");
    return EXIT_SUCCESS;
  } else {
    printf("Units without an IP:\n%s\n\n", buf);
  }
#endif
  if (!req_mac(macbuf)) {
    fprintf(stderr, "'%s' is not a valid MAC-address.\n", macbuf);
    return EXIT_FAILURE;
  }
  if (!req_ip(ipbuf)) {
    fprintf(stderr, "'%s' is not a valid IPv4 address.\n", ipbuf);
    return EXIT_FAILURE;
  }

  printf("Assign ip '%s' to device with MAC-address '%s'?\n[y/n] ", ipbuf, macbuf);
  if ((c = getchar()) == 'y') {
    printf("Assigning ip as requested by the user.\n");
#ifdef HAS_GCLIB
    check(GAssign(ipbuf, macbuf));
#endif
  } else {
    printf("Not assigning ip as requested by the user. You may run this\n"
	   "program again when you want to assign an ip to the device.\n");
    return EXIT_SUCCESS;
  }   
#ifdef HAS_GCLIB
  check(GAddresses(buf, BFR_SIZE));
  printf("Available addresses:\n%s\n\n", buf);
#endif
  printf("The device should now be visible in GalilTools. Note that you\n"
	 "may have to try to connect to it twice before you succeed.\n");
  return 0;
}

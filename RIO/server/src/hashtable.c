/* From K&R 2nd edition, Chapter 6.6 Table Lookup */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "hashtable.h"

typedef void *(val_func)(void *);

/**
 * Maximum length of keys.
 */
#define KEYLEN 16

/**
 * Hash table bin list entry.
 */
struct nlist {
  struct nlist *next;
  char key[KEYLEN+1];
  val_func *val;
};

/**
 * Number of bins to use in the hash table.
 */
#define HASHSIZE 101

/**
 * Hash table object.
 */
struct hash_table {
  struct nlist *tab[HASHSIZE];
};

/**
 * Create a hash of s in the range 0 <= hash < HASHSIZE.
 */
static unsigned
hash(char const *s)
{
  if (!s) {
    return 0;
  }
  
  unsigned hashval = 0;
  while (*s) {
    hashval = *s++ + 31 * hashval;
  }
  return hashval % HASHSIZE;
}

/**
 * Find the entry associated with key.
 */
static struct nlist *
lookup(struct hash_table *self,
       char const *key)
{
  struct nlist *np = self->tab[hash(key)];
  for (; np; np = np->next) {
    if (strncmp(key, np->key, KEYLEN) == 0) {
      return np;
    }
  }
  return NULL;
}

/**
 * Insert val and its key into the hash table.
 */
static struct nlist *
install(struct hash_table *self,
	char const *key,
	val_func *val)
{
  struct nlist *np = lookup(self, key);
  if (!np) {
    np = (struct nlist *) calloc(1, sizeof(struct nlist));
    if (!np) {
      return NULL;
    }
    strncpy(np->key, key, KEYLEN);
    unsigned hashval = hash(key);
    np->next = self->tab[hashval];
    self->tab[hashval] = np;
  }
  np->val = val;
  return np;
}

/**
 * Remove the entry assocated with key from the hash table.
 */
static void
undef(struct hash_table *self,
      char const *key)
{
  unsigned hashval = hash(key);
  struct nlist *np = self->tab[hashval];
  if (!np) {
    return;
  }
  if (strncmp(key, np->key, KEYLEN) == 0) {
    self->tab[hashval] = np->next;
    free(np);
    return;
  }
  for (; np->next; np = np->next) {
    if (strncmp(key, np->next->key, KEYLEN) == 0) {
      struct nlist *p = np->next;
      np->next = p->next;
      free(np);
      return;
    }
  }
}

/**
 * Allocate space for the hash table.
 */
static struct hash_table *
create_table(void)
{
  return (struct hash_table *) calloc(1, sizeof(struct hash_table));
}

/**
 * Remove all entries from the hash table and deallocate the hash table.
 */
static void
destroy_table(struct hash_table *self)
{
  if (!self) {
    return;
  }
  struct nlist **p, **end;
  for (p = self->tab, end = self->tab + HASHSIZE; p != end; ++p) {
    while (*p) {
      undef(self, (*p)->key);
    }
  }
  free(self);
}

GetterMap *
GetterMap_new(void)
{
  return (GetterMap *) create_table();
}

void
GetterMap_delete(GetterMap *self)
{
  destroy_table((struct hash_table *)self);
}

void
GetterMap_put(GetterMap *self,
	      char const *key,
	      val_getter *val)
{
  install((struct hash_table *)self, key, (val_func *)val);
}

val_getter *
GetterMap_get(GetterMap *self,
	      char const *key)
{
  struct nlist *p = lookup((struct hash_table *)self, key);
  return (val_getter *) (p ? p->val : NULL);
}


SetterMap *
SetterMap_new(void)
{
  return (SetterMap *) create_table();
}

void
SetterMap_delete(SetterMap *self)
{
  destroy_table((struct hash_table *)self);
}

void
SetterMap_put(SetterMap *self,
	      char const *key,
	      val_setter *val)
{
  install((struct hash_table *)self, key, (val_func *)val);
}

val_setter *
SetterMap_get(SetterMap *self,
	      char const *key)
{
  struct nlist *p = lookup((struct hash_table *)self, key);
  return (val_setter *) (p ? p->val : NULL);
}

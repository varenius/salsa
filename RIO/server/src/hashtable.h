#ifndef HASHTABLE_H_INCLUDED
#define HASHTABLE_H_INCLUDED

#include "rio.h"

typedef struct getter_map GetterMap;
typedef double (val_getter)(RIO *);

/**
 * Create a new hash table for getter functions.
 */
GetterMap *GetterMap_new(void);

/**
 * Destroy a hash table for getter functions.
 */
void GetterMap_delete(GetterMap *self);

/**
 * Insert the getter function and associate it with key.
 */
void GetterMap_put(GetterMap *self, char const *key, val_getter *val);

/**
 * Retrieve the getter function associated with key.
 */
val_getter *GetterMap_get(GetterMap *self, char const *key);


typedef struct setter_map SetterMap;
typedef void (val_setter)(RIO *, double);

/**
 * Create a new hash table for setter functions.
 */
SetterMap *SetterMap_new(void);

/**
 * Destroy a hash table for setter functions.
 */
void SetterMap_delete(SetterMap *self);

/**
 * Insert the setter function and associate it with key.
 */
void SetterMap_put(SetterMap *self, char const *key, val_setter *val);

/**
 * Retrieve the setter function associated with key.
 */
val_setter *SetterMap_get(SetterMap *self, char const *key);

#endif /* HASHTABLE_H_INCLUDED */

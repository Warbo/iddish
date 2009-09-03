
  // Import the Id object model
  #include "obj.c"


  // Now define the namespace type
  struct namespace
  {
    struct vtable  *_vt[0];
    int             size;
    int             tally;
    struct object **keys;
    struct object **values;
    struct vtable  *parent;
    struct namespace *parent_namespace;
  };

// // Define our functions first
//  This needs to exist now, although it won't be assigned until later
struct object *s_namespace_lookup;
//  This function searches its object (a namespace) for a symbol
//  representing the given string. If found then it is returned.


struct object *function_namespace_lookup(struct closure *closure, struct object *self, char* string) {
	struct object *symbol;

    int i;
    for (i = 0; i < ((struct vtable *)self)->tally; ++i)
      {
        symbol = ((struct vtable *)self)->keys[i];
        if (!strcmp(string, ((struct symbol *)symbol)->string))
          return symbol;
      }
    symbol = 0;
    symbol = send(((struct namespace *)self)->parent_namespace, s_namespace_lookup, string);
    return symbol;
  
	}


struct object *function_toplevel_namespace_lookup(struct closure *closure, struct object *self, char* string) {
	struct object *symbol;
//  This will store our symbol if we find it

    // Loop through every key in this vtable (which we've hijacked to
    // implement our namespace dictionary)
    int i;
    for (i = 0; i < ((struct vtable *)self)->tally; ++i)
      {
        symbol = ((struct vtable *)self)->keys[i];
        // Compare the string which this symbol represents with the 
        // string we've been given.
        if (!strcmp(string, ((struct symbol *)symbol)->string)) {
          // Return if we've found a match
          return symbol;
        }
      }
    // If we've got this far without returning then the toplevel
    // namespace doesn't contain such a symbol, and since we can't look
    // any higher up all we can do is return a null pointer
    symbol = 0;
    return symbol;
  
	}
//  This looks for a symbol matching the given string in the current
//  object (a namespace) and its direct ancestors and returns it. If it
//  is not found then a new symbol is made for it in the current object.


struct object *function_namespace_intern(struct closure *closure, struct object *self, char* string) {
	struct object *symbol;
//  This will eventually store the symbol

    symbol = send(self, s_namespace_lookup, string);
    if (symbol == 0) {
      symbol = symbol_new(string);
      send(self, s_addMethod, symbol, 0);
    }
    return symbol;
  
	}


  int main(void) {
    //// Begin with some initialisation stuff
  
    // Initialise Id
    init();


    // Rename the root object's vtable to fit our naming scheme
    struct vtable *vtable_object = object_vt;
    
  
//  This will store objects we are about to do things to, once they've
//  been extracted from the namespace dictionary
struct object *current_object;
//  We need to use namespaces in order to prevent headaches, which we can
//  do using the symbols and vtables of Id

  // The namespace we are in will always be referenced by this name
  struct namespace *current_namespace;

//  This encapsulates the behaviour of namespaces
struct object *vtable_namespace = send(vtable_vt, s_delegated);
//  This is a special-case for the highest namespace (since it can't
//  defer to parents)
struct object *vtable_toplevel_namespace = send(vtable_namespace, s_delegated);
//  We now need to tell the namespace that it should live below the
//  toplevel namespace

    ((struct namespace *)vtable_namespace)->parent_namespace = (struct namespace *)vtable_toplevel_namespace;
  
//  Make some global symbols so we can bootstrap the namespaces

    struct object *s_namespace_lookup = symbol_intern(0, 0, "namespace_lookup");
    send(vtable_namespace, s_addMethod, s_namespace_lookup, function_namespace_lookup);
  
//  Overwrite lookups for the toplevel namespace using its own function

    send(vtable_toplevel_namespace, s_addMethod, s_namespace_lookup, function_toplevel_namespace_lookup);
  
//  Make some global symbols so we can bootstrap the namespaces

    struct object *s_namespace_intern = symbol_intern(0, 0, "namespace_intern");
    send(vtable_namespace, s_addMethod, s_namespace_intern, function_namespace_intern);
  

  // Set the current namespace
  current_namespace = (struct namespace *)vtable_toplevel_namespace;


  return 0;
  }


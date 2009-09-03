"""This translates the "Iddish" intermediate language to C."""

try:
	import psyco
	psyco.full()
except:
	pass
	
from pymeta.grammar import OMeta
from pymeta.runtime import ParseError
from python_rewriter.base import strip_comments

import sys
sys.setrecursionlimit(1000000)

def function_writer(name, args, code):
	# ALL of our functions have the following signature:
	# pointer-to-object function_<name>(pointer-to-closure closure, pointer-to-object self, ARGS...)
	func = """

struct object *function_"""+name+"""(struct closure *closure, struct object *self"""
	
	if len(args) > 0:
		func = func + ', '
		for arg in args:
			if ' ' in arg:
				func = func + arg + ', '
			else:
				func = func + 'struct object *'+arg+', '
		func = func[:-2]
	func = func + """) {
	"""+code+"""
	}"""
	#struct object *s_"""+name+' = send(current_namespace, s_intern, '+name+""";
	#"""
	return func
	
def method_writer(class_name, method_name, args, code):
	# ALL of our methods have the following signature:
	# pointer-to-object function_<name>(pointer-to-closure closure, pointer-to-object self, ARGS...)
	meth = """

struct object* functionOF"""+class_name+'_'+method_name+"""(struct closure *closure, struct object *self"""
	
	if len(args) > 0:
		meth = meth + ', '
		for arg in args:
			if ' ' in arg:
				meth = meth + arg + ', '
			else:
				meth = meth + 'struct object *'+arg+', '
		meth = meth[:-2]
	meth = meth + """) {
	"""+code+"""
	}"""
	#struct object *sOF"""+class_name+'_'+method_name+' = send(current_namespace, s_intern, '+class_name+'METHOD'+method_name+""");
	#send(vtable_"""+class_name+', s_addMethod, sOF'+class_name+'_'+method_name+', functionOF'+class_name+'_'+method_name+""");
	#"""
	return meth

def message_sender(object, messagename, arguments):
	# All of our objects accept messages sent via:
	# send(object's VTable, message symbol, ARGS...)
	call = """
current_object = send(current_namespace, s_lookup, """+object+""");
send(current_object, s_"""+messagename
	
	if len(arguments) > 0:
		call = call + ', '+', '.join(arguments)
	
	call = call+');'
	
	return call

def function_caller(messagename, arguments):
	code = 'send(current_namespace, symbol_'+messagename
	if len(arguments) > 0:
		code = code + ', '+', '.join(arguments)
	code = code + ');'
	return code

grammar_def = """

# A program is a series of statements
program ::= <statement>+:code											=> \"""\n\""".join(code)

# A space is a space (ie. ' '), a tab or a newline character
space ::= <anything>:a ?(a == ' ' or a == \"""\n\""" or a == '\t')		=> ''

# Whitespace is an arbitrary amount of spaces
whitespace ::= (<space>)*												=> ''

# A statement is a single line of code (where lines end in a semicolon)
statement ::= <whitespace> (<comment> 
                           | <assignment> 
                           | <embedded_c>
                           | <function_def>
                           | <class_def>
                           | <message_send> 
                           | <raw_call> 
                           | <declaration>):stmt						=> stmt

# Comments begin with '//' and end at a newline (careful when using
# character codes in comments such as backslash-n!)
comment ::= '/' '/' <commentbody>:body										=> '// '+body

# This catches everything up to and including a newline
commentbody ::= <anything>:newline ?(newline == \"""\n\""")				=> ''
              | <anything>:start <commentbody>:rest						=> start+rest

# Assignments are the binding of a statement's value to a variable
assignment ::= <name>:variable <whitespace> '=' <whitespace> 
                 <assignment_value>:value								=> variable+' = '+value

assignment_value ::= '(' <name>:n ')'									=> n+';'
                   | <statement>:s										=> s

# Embedded C will simply be inserted into the output unchanged
embedded_c ::= <token 'EMBEDDED_C{{{'> <embedded_c_body>:body			=> body

# This returns everything up to and excluding "}}}END_EMBEDDED_C"
embedded_c_body ::= '}' '}' '}' 'E' 'N' 'D' '_' 'E' 'M' 'B' 'E' 'D' 'D' 
                    'E' 'D' '_' 'C'										=> ''
                  | <anything>:start <embedded_c_body>:rest				=> start+rest

# function_def is the definition of a function
function_def ::= <token 'def'> ' ' <name>:function_name '('
                 <arg>*:arguments ')' <token '{'> <statement>*:code
                 <token '}'> <whitespace>								=> function_writer(function_name, arguments, \"""\n\""".join(code))

# method_def is the definition of a function belonging to an object
method_def ::= <token 'def'> <whitespace> <name>:class_name '.' 
               <name>:method_name '(' <arg>*:arguments ')' <token '{'>
               <statement>*:code <token '}'> <whitespace>				=> method_writer(class_name, method_name, arguments, code)

# Class definitions simply declare that a class exists, methods for
# classes are defined using the method_def syntax foo.bar(args){code}
class_def ::= <token 'class '> <name>:classname '(' <name>:parent ')'	=> 'struct object *vtable_'+classname+' = send(vtable_'+parent+', s_delegated);'
            | <token 'class '> <name>									=> 'struct object *vtable_'+classname+' = send(vtable_object, s_delegated);'

# Message send is the calling of an object's function, ie. a method call
message_send ::= <name>:o '.' <name>:m '(' <arg>*:a ')'					=> message_sender(o, m, a)

# A raw call is the calling of a function which isn't owned by an object
raw_call ::= <name>:m '(' <arg>*:a ')'									=> function_caller(m, a)

# A declaration declares a new object variable
declaration ::= <name>:n 												=> 'struct object *'+n+';'

# Arg is an argument to a function
arg ::= <name>:type ' ' <name>:binding ','*								=> type+'* '+binding
      | <name>:variable ','*											=> variable

# A name is a valid variable, function or class name
name ::= <startchar>:start <namechar>*:rest								=> start+''.join(rest)

# These are valid at the start of a name
startchar ::= 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'I' | 'J' 
            | 'K' | 'L' | 'M' | 'N' | 'O' | 'P' | 'Q' | 'R' | 'S' | 'T' 
            | 'U' | 'V' | 'W' | 'X' | 'Y' | 'Z' | 'a' | 'b' | 'c' | 'd' 
            | 'e' | 'f' | 'g' | 'h' | 'i' | 'j' | 'k' | 'l' | 'm' | 'n' 
            | 'o' | 'p' | 'q' | 'r' | 's' | 't' | 'u' | 'v' | 'w' | 'x' 
            | 'y' | 'z' | '_'

# These are valid anywhere after the start of a name
namechar ::= <startchar> | '0' | '1' | '2' | '3' | '4' | '5' | '6' 
           | '7' | '8' | '9'

"""

test = """

EMBEDDED_C{{{
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
}}}END_EMBEDDED_C

//// Define our functions first

// This needs to exist now, although it won't be assigned until later
s_namespace_lookup

// This function searches its object (a namespace) for a symbol
// representing the given string. If found then it is returned.
def namespace_lookup(char string)
{
  symbol
  EMBEDDED_C{{{
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
  }}}END_EMBEDDED_C
}

def toplevel_namespace_lookup(char string)
{
  symbol		// This will store our symbol if we find it
  EMBEDDED_C{{{
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
  }}}END_EMBEDDED_C
}

// This looks for a symbol matching the given string in the current
// object (a namespace) and its direct ancestors and returns it. If it
// is not found then a new symbol is made for it in the current object.
def namespace_intern(char string)
{
  symbol		// This will eventually store the symbol
  EMBEDDED_C{{{
    symbol = send(self, s_namespace_lookup, string);
    if (symbol == 0) {
      symbol = symbol_new(string);
      send(self, s_addMethod, symbol, 0);
    }
    return symbol;
  }}}END_EMBEDDED_C
}

EMBEDDED_C{{{

  int main(void) {
    //// Begin with some initialisation stuff
  
    // Initialise Id
    init();


    // Rename the root object's vtable to fit our naming scheme
    struct vtable *vtable_object = object_vt;
    
  }}}END_EMBEDDED_C
  
  // This will store objects we are about to do things to, once they've
  // been extracted from the namespace dictionary
  current_object
  
  // We need to use namespaces in order to prevent headaches, which we can
  // do using the symbols and vtables of Id

EMBEDDED_C{{{
  // The namespace we are in will always be referenced by this name
  struct namespace *current_namespace;
}}}END_EMBEDDED_C

  // This encapsulates the behaviour of namespaces
  class namespace(vt)

  // This is a special-case for the highest namespace (since it can't
  // defer to parents)
  class toplevel_namespace(namespace)

  // We now need to tell the namespace that it should live below the
  // toplevel namespace
  EMBEDDED_C{{{
    ((struct namespace *)vtable_namespace)->parent_namespace = (struct namespace *)vtable_toplevel_namespace;
  }}}END_EMBEDDED_C

  // Make some global symbols so we can bootstrap the namespaces

  EMBEDDED_C{{{
    struct object *s_namespace_lookup = symbol_intern(0, 0, "namespace_lookup");
    send(vtable_namespace, s_addMethod, s_namespace_lookup, function_namespace_lookup);
  }}}END_EMBEDDED_C

  // Overwrite lookups for the toplevel namespace using its own function

  EMBEDDED_C{{{
    send(vtable_toplevel_namespace, s_addMethod, s_namespace_lookup, function_toplevel_namespace_lookup);
  }}}END_EMBEDDED_C

  // Make some global symbols so we can bootstrap the namespaces

  EMBEDDED_C{{{
    struct object *s_namespace_intern = symbol_intern(0, 0, "namespace_intern");
    send(vtable_namespace, s_addMethod, s_namespace_intern, function_namespace_intern);
  }}}END_EMBEDDED_C

EMBEDDED_C{{{
  // Set the current namespace
  current_namespace = (struct namespace *)vtable_toplevel_namespace;
}}}END_EMBEDDED_C

EMBEDDED_C{{{
  return 0;
  }
}}}END_EMBEDDED_C

"""

params = globals()
for key in locals().keys():
	params[key] = locals()[key]

grammar = OMeta.makeGrammar(strip_comments(grammar_def), params)

matcher = grammar(test)
print matcher.apply('program')

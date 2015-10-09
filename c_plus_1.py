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

grammar_def = """

# A program is a series of statements
program ::= <statement>+:code											=> \"""\n\""".join(code)

# A space is a space (ie. ' '), a tab or a newline character
space ::= <anything>:a ?(a == ' ' or a == \"""\n\""" or a == '\t')		=> ''

# Whitespace is an arbitrary amount of spaces
whitespace ::= (<space>)*												=> ''

# A statement is a single line of code
statement ::= <whitespace> (<comment> 
                           | <assignment> 
                           | <embedded_c>
                           | <function_def>
                           | <message_send> 
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
function_def ::= <token 'def'> ' ' <name>:object '.'
                 <name>:function_name '(' <defarg>*:arguments ')' 
                 <token '{'> <statement>*:code <token '}'> <whitespace>	=> 'struct object *'+function_name+'(struct closure *closure, struct vtable *self'+', '.join(['']+arguments)+') {'+code+\"""}\ns_\"""+function_name+' = symbol_intern(0, 0, "'+function_name+'");'+\"""\nsend(vt_\"""+object+', s_addMethod, s_'+function_name+', '+function_name+\""");\n\"""

# Defarg is an argument to a function definition
defarg ::= <whitespace> <name>:binding ','								=> 'struct object *'+binding
         | <whitespace> <name>:binding									=> 'struct object *'+binding


# Message send is the calling of an object's function, ie. a method call
message_send ::= <name>:o '.' <name>:m '(' <callarg>*:a ')'				=> 'send('+o+', s_'+m+''.join(['']+a)+\""");\n\"""

# Callarg is an argument to a function call
callarg ::= <whitespace> <name>:binding ','								=> binding
          | <whitespace> <name>:binding									=> binding

# A declaration declares a new object variable
declaration ::= <name>:n 												=> 'struct object *'+n+';'

# A name is a valid variable or function name
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

environment_initialiser = """

  // Import the Id object model
  #include "obj.c"

"""

program_initialiser = """
  int main(void) {
    //// Begin with some initialisation stuff
  
    // Initialise Id
    init();
"""

program_end = """

  return 0;
  }

"""

params = globals()
for key in locals().keys():
	params[key] = locals()[key]

grammar = OMeta.makeGrammar(strip_comments(grammar_def), params)

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print "Usage: c_plus_1.py input.c1 [output.c]"
		sys.exit()

	in_name = sys.argv[1]
	if len(sys.argv) > 2:
		out_name = sys.argv[2]
	else:
		out_name = in_name.rsplit('.', 1)[0]+'.c'
	
	in_file = open(in_name, 'r')
	environment_in = ''
	program_in = ''
	in_program = False
	for l in in_file.readlines():
		if l.strip() == '[[[':
			pass
		elif l.strip() == ']]]':
			in_program = True
		else:
			if in_program:
				program_in = program_in + l
			else:
				environment_in = environment_in + l
	in_file.close()

	environment_matcher = grammar(environment_in)
	program_matcher = grammar(program_in)
	
	out_file = open(out_name, 'w')
	out_file.write(environment_initialiser)
	out_file.write(environment_matcher.apply('program'))
	out_file.write(program_initialiser)
	out_file.write(program_matcher.apply('program'))
	out_file.write(program_end)
	out_file.close()

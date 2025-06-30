program
    : PROGRAM COLON ID SEMICOLON declarations methods_list main_method END
    ;

declarations
    : DECIDS COLON var_declaration+
    | empty
    ;

var_declaration
    : ID (COMMA ID)* COLON type SEMICOLON           # Declaração de grupo
    | ID COLON type SEMICOLON                       # Declaração única
    | ID ASSIGN expression SEMICOLON                # Atribuição de constante
    ;

type
    : INT
    | FLOAT
    | BOOL
    | STR
    ;

methods_list
    : method_declaration*
    ;

method_declaration
    : type_or_void ID LPAREN parameters_list RPAREN LBRACE block_content RBRACE
    ;

type_or_void
    : type
    | VOID
    ;

parameters_list
    : parameter (COMMA parameter)*
    | empty
    ;

parameter
    : type ID
    ;

main_method
    : MAIN COLON block_content
    ;

block_content
    : declarations statements
    | declarations
    | statements
    | empty
    ;

statements
    : statement+
    ;

statement
    : assignment SEMICOLON
    | if_statement
    | while_statement
    | for_statement
    | print_statement
    | input_statement
    | return_statement
    | break_statement
    | block_statement
    | function_call SEMICOLON
    ;

assignment
    : ID ASSIGN expression
    | ID INCREMENT
    | ID DECREMENT
    ;

if_statement
    : IF LPAREN condition RPAREN block_statement (ELSE block_statement)?
    ;

while_statement
    : WHILE LPAREN condition RPAREN block_statement
    ;

for_statement
    : FOR LPAREN assignment SEMICOLON condition SEMICOLON assignment RPAREN block_statement
    ;

print_statement
    : PRINT LPAREN expression_list RPAREN SEMICOLON
    ;

input_statement
    : INPUT LPAREN ID (COMMA ID)* RPAREN SEMICOLON
    ;

return_statement
    : RETURN expression SEMICOLON
    ;

break_statement
    : BREAK SEMICOLON
    ;

block_statement
    : LBRACE block_content RBRACE
    ;

condition
    : expression comparison expression
    | NOT expression
    ;

comparison
    : EQUALS
    | NEQUALS
    | GT
    | LT
    ;

expression
    : expression PLUS term
    | expression MINUS term
    | term
    ;

term
    : term TIMES factor
    | term DIVIDE factor
    | factor
    ;

factor
    : MINUS factor %prec UMINUS
    | LPAREN expression RPAREN
    | ID
    | NUMBER
    | STRING_LITERAL
    | BOOLEAN_LITERAL
    | function_call
    ;

function_call
    : ID LPAREN expression_list RPAREN
    ;

expression_list
    : expression (COMMA expression)*
    ;

empty
    : /* nothing */
    ;

// Tokens (adicionais ou corrigidos)
ID : [a-zA-Z_][a-zA-Z_0-9]*
NUMBER : \d*\.?\d+
STRING_LITERAL : "([^"\\]|\\.)*"
BOOLEAN_LITERAL : 'true' | 'false'
COMMENT : '//' .*
WS : [ \t\n]+